import hashlib
import hmac
import json
import time
import re
from pathlib import Path
from uuid import UUID, uuid4
from datetime import datetime, timezone
from typing import Literal
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy.exc import IntegrityError
from starlette.concurrency import run_in_threadpool
from app.config import settings
from app.db import engine, query, one, rows, audit
from app import schemas as S
from app.channel import signed, receive
from app.providers import reset_turn_result, turn_result
from app.operations import visible, transition, declared_items
from app.analytics import record, report
from app.worker import process

cfg = settings()
app = FastAPI(title="EcoConecta · Villas de San Pablo", version="0.1.0")
static = Path(__file__).parent / "static"
buckets = {}


@app.middleware("http")
async def limits(request, call_next):
    now = int(time.monotonic() // 60)
    addr = request.client.host if request.client else "local"
    if buckets.get("minute") != now:
        buckets.clear()
        buckets["minute"] = now
    count = buckets.get(addr, 0) + 1
    if count > 240 or len(buckets) > 10000:
        return JSONResponse({"detail": "Intenta de nuevo en un minuto"}, 429)
    buckets[addr] = count
    response = await call_next(request)
    response.headers.update(
        {
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
            "Referrer-Policy": "no-referrer",
        }
    )
    if request.url.path.startswith("/panel"):
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; frame-ancestors 'none'; form-action 'none'"
        )
    return response


@app.exception_handler(IntegrityError)
async def invalid_constraint(request, exc):
    return JSONResponse(
        {"detail": "El registro no cumple las reglas del servicio"}, 409
    )


@app.exception_handler(RequestValidationError)
async def invalid_input(request, exc):
    return JSONResponse({"detail": "Verifica el formato y los campos enviados"}, 422)


def session():
    with engine.begin() as db:
        yield db


bearer = HTTPBearer(auto_error=False)


def actor(
    auth: HTTPAuthorizationCredentials | None = Depends(bearer), db=Depends(session)
):
    digest = hashlib.sha256((auth.credentials if auth else "").encode()).hexdigest()
    u = one(
        db,
        "SELECT id,handle,role,flow FROM users WHERE active AND token_hash=:t",
        t=digest,
    )
    if not u:
        raise HTTPException(
            401, "Acceso restringido", headers={"WWW-Authenticate": "Bearer"}
        )
    return u


def staff(u=Depends(actor)):
    if u["role"] == "resident":
        raise HTTPException(403, "Acceso para el equipo operativo")
    return u


def admin(u=Depends(staff)):
    if u["role"] != "admin":
        raise HTTPException(403, "Acceso administrativo")
    return u


@app.get("/health")
def health(db=Depends(session)):
    query(db, "SELECT 1 FROM alembic_version")
    return {
        "status": "ok",
        "channel": cfg.channel,
        "ai": cfg.ai,
        "environment": cfg.env,
    }


@app.get("/panel", include_in_schema=False)
def panel():
    return FileResponse(static / "panel.html")


@app.get("/panel/{asset}", include_in_schema=False)
def assets(asset: Literal["panel.css", "panel.js"]):
    return FileResponse(static / asset)


@app.get("/api/v1/me")
def me(u=Depends(actor)):
    return dict(u)


@app.post("/api/v1/demo/messages")
def demo_message(m: S.Message, u=Depends(actor), db=Depends(session)):
    if cfg.env not in ("demo", "test") or cfg.channel != "mock":
        raise HTTPException(404)
    if u["role"] != "resident":
        raise HTTPException(403)
    reset_turn_result()
    key = f"demo:{u['id']}:{m.message_id or uuid4()}"
    row = receive(db, u["id"], key, m.kind, m.text, datetime.now(timezone.utc))
    if not row:
        return {"duplicate": True, "ai": None}
    answer = process(db, one(db, "SELECT * FROM messages WHERE id=:id", id=row["id"]))
    return {"reply": answer, "simulation": True, "ai": turn_result()}


HOOK = "/api/v1/integrations/whatsapp/webhook"


@app.get(HOOK, response_class=PlainTextResponse)
def verify(request: Request):
    p = request.query_params
    if (
        not cfg.verify
        or p.get("hub.mode") != "subscribe"
        or not hmac.compare_digest(
            p.get("hub.verify_token", "").encode(), cfg.verify.encode()
        )
    ):
        raise HTTPException(403)
    return p.get("hub.challenge", "")


class WMessage(BaseModel):
    id: str = Field(min_length=1, max_length=256)
    sender: str = Field(alias="from", pattern=r"^\d{6,18}$")
    timestamp: int = Field(gt=0, lt=4102444800)
    type: str
    text: dict | None = None
    audio: dict | None = None


def ingest(data):
    with engine.begin() as db:
        for entry in data.get("entry", []):
            if entry.get("id") != cfg.account:
                continue
            for change in entry.get("changes", []):
                val = change.get("value", {})
                if (
                    change.get("field") != "messages"
                    or val.get("metadata", {}).get("phone_number_id") != cfg.phone_id
                ):
                    continue
                for status in val.get("statuses", []):
                    state = status.get("status")
                    if state in ("delivered", "read", "failed"):
                        changed = query(
                            db,
                            """UPDATE notifications SET state=:s WHERE external_id=:x
                          AND (state='sent' OR (state='delivered' AND :s='read'))""",
                            s=state,
                            x=status.get("id"),
                        )
                        if changed.rowcount and state == "failed":
                            record(
                                db,
                                "whatsapp_delivery_failure",
                                channel="meta",
                                state="failed",
                            )
                for raw in val.get("messages", []):
                    m = WMessage.model_validate(raw)
                    u = one(
                        db,
                        "SELECT id,role FROM users WHERE active AND phone=:p",
                        p=m.sender,
                    )
                    if not u:
                        continue
                    stamp = min(
                        datetime.fromtimestamp(m.timestamp, timezone.utc),
                        datetime.now(timezone.utc),
                    )
                    if u["role"] != "resident":
                        query(
                            db,
                            "UPDATE users SET last_inbound=greatest(last_inbound,:s) WHERE id=:u",
                            u=u["id"],
                            s=stamp,
                        )
                        continue
                    payload = (
                        (m.text or {}).get("body", "")
                        if m.type == "text"
                        else (m.audio or {}).get("id", "")
                    )
                    if not isinstance(payload, str) or len(payload) > 2000:
                        continue
                    inserted = receive(
                        db,
                        u["id"],
                        m.id,
                        m.type if m.type in ("audio", "text") else "unsupported",
                        payload,
                        stamp,
                    )
                    record(
                        db,
                        "webhook_received" if inserted else "webhook_duplicate",
                        channel="meta",
                    )


def log_webhook_error(reason):
    with engine.begin() as db:
        record(db, "webhook_error", channel="meta", reason=reason)


@app.post(HOOK)
async def webhook(request: Request):
    if not all((cfg.secret, cfg.phone_id, cfg.account)):
        raise HTTPException(503, "Webhook sin configurar")
    body = bytearray()
    async for chunk in request.stream():
        if len(body) + len(chunk) > 256000:
            await run_in_threadpool(log_webhook_error, "body_too_large")
            raise HTTPException(413)
        body.extend(chunk)
    signature = request.headers.get("x-hub-signature-256", "")
    if not re.fullmatch(r"sha256=[0-9a-f]{64}", signature) or not signed(
        body, signature
    ):
        await run_in_threadpool(log_webhook_error, "invalid_signature")
        raise HTTPException(403)
    try:
        obj = json.loads(body)
        if obj.get("object") != "whatsapp_business_account":
            raise ValueError()
        await run_in_threadpool(ingest, obj)
    except (ValidationError, TypeError, ValueError, AttributeError):
        await run_in_threadpool(log_webhook_error, "invalid_payload")
        raise HTTPException(400, "Evento inválido")
    return {"received": True}


@app.get("/api/v1/requests")
def inbox(flow: S.Flow | None = None, u=Depends(staff), db=Depends(session)):
    return rows(
        db,
        """SELECT r.id,r.status,r.flow,r.material,r.quantity,r.unit,r.created_at,
        (SELECT array_agg(i.material ORDER BY i.material) FROM collection_request_items i WHERE i.request_id=r.id) AS materials
        FROM collection_requests r LEFT JOIN assignments a ON a.request_id=r.id
        WHERE (CAST(:f AS text) IS NULL OR r.flow=:f) AND (:role='admin'
        OR (:role='coordinator' AND r.flow=:scope) OR (:role='collector' AND a.collector_id=:uid))
        ORDER BY r.created_at DESC LIMIT 150""",
        f=flow,
        role=u["role"],
        scope=u["flow"],
        uid=u["id"],
    )


@app.get("/api/v1/requests/{rid}")
def details(rid: UUID, u=Depends(actor), db=Depends(session)):
    r = dict(visible(db, rid, u))
    if u["role"] in {"coordinator", "collector"} and r["status"] not in {
        "recolectada",
        "cancelada",
    }:
        r["contact"] = one(db, "SELECT phone FROM users WHERE id=:u", u=r["owner_id"])[
            "phone"
        ]
    r["items"] = declared_items(db, rid)
    r["history"] = rows(
        db,
        "SELECT status,at FROM request_status_history WHERE request_id=:r ORDER BY id",
        r=rid,
    )
    return r


@app.get("/api/v1/alerts")
def alerts(u=Depends(staff), db=Depends(session)):
    return rows(
        db,
        """SELECT a.id,a.kind,a.flow,a.request_id,a.at,
          CASE WHEN :role='admin' AND a.request_id IS NULL THEN u.handle END AS contact_name,
          CASE WHEN :role='admin' AND a.request_id IS NULL THEN u.phone END AS contact
          FROM alerts a JOIN users u ON u.id=a.user_id WHERE :role='admin' OR
         (:role='coordinator' AND a.flow=:f) ORDER BY a.id DESC LIMIT 100""",
        role=u["role"],
        f=u["flow"],
    )


@app.get("/api/v1/collectors")
def collectors(u=Depends(staff), db=Depends(session)):
    return rows(
        db,
        "SELECT id,handle,flow FROM users WHERE active AND role='collector' AND (:r='admin' OR flow=:f) ORDER BY handle",
        r=u["role"],
        f=u["flow"],
    )


@app.post("/api/v1/requests/{rid}/assign")
def assign(rid: UUID, data: S.Assignment, u=Depends(staff), db=Depends(session)):
    return transition(db, rid, u, "assign", data)


@app.post("/api/v1/requests/{rid}/schedule")
def schedule(rid: UUID, data: S.Schedule, u=Depends(staff), db=Depends(session)):
    return transition(db, rid, u, "schedule", data)


@app.post("/api/v1/requests/{rid}/collect")
def collect(rid: UUID, data: S.Collection, u=Depends(staff), db=Depends(session)):
    return transition(db, rid, u, "collect", data)


@app.get("/api/v1/admin/metrics")
def metrics(u=Depends(admin), db=Depends(session)):
    return report(db)


@app.post("/api/v1/admin/events")
def event(data: S.Event, u=Depends(admin), db=Depends(session)):
    r = one(
        db,
        """INSERT INTO events(kind,title,description,starts_at,place,organizer,category,published)
         VALUES(:kind,:title,:description,:starts_at,:place,:organizer,:category,:published) RETURNING id""",
        **data.model_dump(),
    )
    audit(db, u["id"], "event", r["id"])
    return r


@app.post("/api/v1/admin/articles")
def article(data: S.Article, u=Depends(admin), db=Depends(session)):
    r = one(
        db,
        """INSERT INTO articles(title,keywords,answer,source,reviewer,published) VALUES(:title,:keywords,:answer,:source,:by,:published)
      ON CONFLICT(title) DO UPDATE SET keywords=:keywords,answer=:answer,source=:source,reviewer=:by,published=:published,version=articles.version+1,reviewed_at=now()
      RETURNING id,version""",
        by=u["handle"],
        **data.model_dump(),
    )
    audit(db, u["id"], "article", r["id"])
    return r


@app.get("/api/v1/admin/articles")
def list_articles(u=Depends(admin), db=Depends(session)):
    return rows(db, "SELECT * FROM articles ORDER BY title LIMIT 200")


@app.post("/api/v1/admin/materials")
def material(data: S.Material, u=Depends(admin), db=Depends(session)):
    r = one(
        db,
        """INSERT INTO materials(name,flow,accepted) VALUES(:name,:flow,:accepted)
      ON CONFLICT(name) DO UPDATE SET accepted=:accepted WHERE materials.flow=:flow RETURNING name""",
        **data.model_dump(),
    )
    if not r:
        raise HTTPException(409, "El material ya pertenece a otro flujo")
    audit(db, u["id"], "material", data.name)
    return r


@app.post("/api/v1/admin/points-rules")
def rule(data: S.Rule, u=Depends(admin), db=Depends(session)):
    r = one(
        db,
        """INSERT INTO points_rules(material,unit,rate,starts_at,ends_at,approved_by)
       VALUES(:material,:unit,:rate,:starts_at,:ends_at,:by) RETURNING id""",
        by=u["id"],
        **data.model_dump(),
    )
    audit(db, u["id"], "points_rule", r["id"])
    return r

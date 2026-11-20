from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Query
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import text

from .auth import Actor
from .db import engine

router = APIRouter(tags=["Solicitudes"])
Flow = Literal["organico", "reciclable"]
Status = Literal["recibida", "en_revision", "asignada", "programada", "recolectada", "cancelada"]
COORDINATORS = {"coordinador_huerteros": "organico", "coordinador_recicladores": "reciclable"}


class CreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    generator: Literal["hogar", "unidad_productiva"]
    flow: Flow
    zone_id: UUID
    contact_phone: str = Field(pattern=r"^\+[1-9][0-9]{6,14}$")
    address: str = Field(min_length=1, max_length=250)
    preferred_time: str = Field(min_length=1, max_length=150)
    observations: str | None = Field(default=None, max_length=1000)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)

    @model_validator(mode="after")
    def coordinate_pair(self):
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("Se requieren ambas coordenadas.")
        return self


class Summary(BaseModel):
    id: UUID
    code: str
    flow: Flow
    zone_id: UUID
    status: Status
    created_at: datetime


class History(BaseModel):
    to_status: Status
    reason: str | None = None
    changed_at: datetime


class Detail(Summary):
    collector_id: UUID | None
    collector_name: str | None
    scheduled_start: datetime | None
    scheduled_end: datetime | None
    generator: str
    observations: str | None
    preferred_time: str | None
    contact_phone: str
    address: str
    history: list[History]


class Zone(BaseModel):
    id: UUID
    name: str


FIELDS = "r.id, r.code, r.flow, r.zone_id, r.status, r.created_at"
# Explicit coordinator zone grants are separate from collectors' service coverage.
COORD_SCOPE = """
    r.flow::text = :coord_flow AND EXISTS (
        SELECT 1 FROM collective_members m WHERE m.collective_id=r.collective_id
        AND m.user_id=:actor AND m.member_role='coordinador'
        AND EXISTS (SELECT 1 FROM coordinator_zones z WHERE z.member_id=m.id AND z.zone_id=r.zone_id)
    )
"""


@router.get("/zones", response_model=list[Zone])
def zones(actor: Actor):
    with engine().connect() as conn:
        return conn.execute(text("SELECT id,name FROM zones WHERE is_active ORDER BY name,id")).mappings().all()


@router.post("/requests", status_code=201, response_model=Summary)
def create_request(body: CreateRequest, actor: Actor):
    if actor.role != "solicitante":
        raise HTTPException(403, "forbidden")
    with engine().begin() as conn:
        if not conn.scalar(text("SELECT id FROM zones WHERE id=:id AND is_active FOR SHARE"), {"id": body.zone_id}):
            raise HTTPException(422, "inactive_zone")
        collective = conn.scalar(text("SELECT id FROM collectives WHERE flow=:flow"), {"flow": body.flow})
        if not collective:
            raise HTTPException(409, "flow_unconfigured")
        row = conn.execute(text("""
            INSERT INTO pickup_requests AS r
                (code,requester_id,collective_id,flow,zone_id,generator,contact_phone,address,
                 preferred_time,observations,latitude,longitude,source_channel)
            VALUES (:code,:actor,:collective,:flow,:zone_id,:generator,:contact_phone,:address,
                    :preferred_time,:observations,:latitude,:longitude,'web')
            RETURNING """ + FIELDS), {
            **body.model_dump(), "actor": actor.id, "collective": collective,
            "code": "SR-" + uuid4().hex,
        }).mappings().one()
        conn.execute(text("""
            INSERT INTO request_status_history(request_id,to_status,changed_by)
            VALUES (:id,'recibida',:actor)
        """), {"id": row["id"], "actor": actor.id})
        return row


@router.get("/coordinator/requests", response_model=list[Summary])
def inbox(actor: Actor, flow: Flow | None = None, status: Status | None = None,
          zone_id: UUID | None = None, start: AwareDatetime | None = None, end: AwareDatetime | None = None,
          limit: Annotated[int, Query(ge=1, le=100)] = 30,
          offset: Annotated[int, Query(ge=0)] = 0):
    if actor.role not in COORDINATORS:
        raise HTTPException(403, "forbidden")
    clauses = [COORD_SCOPE]
    params = {"coord_flow": COORDINATORS[actor.role], "actor": actor.id, "limit": limit, "offset": offset}
    if start and end and start >= end:
        raise HTTPException(422,"invalid_period")
    if start:
        clauses.append("r.created_at>=:start")
        params["start"] = start
    if end:
        clauses.append("r.created_at<:end")
        params["end"] = end
    for column, value in (("flow", flow), ("status", status), ("zone_id", zone_id)):
        if value is not None:
            clauses.append(f"r.{column}=:{column}")
            params[column] = value
    with engine().connect() as conn:
        return conn.execute(text(f"SELECT {FIELDS} FROM pickup_requests r WHERE " +
            " AND ".join(clauses) + " ORDER BY r.created_at DESC,r.id LIMIT :limit OFFSET :offset"), params).mappings().all()


@router.get("/requests/{request_id}", response_model=Detail)
def detail(request_id: UUID, actor: Actor):
    scopes = {
        "solicitante": "r.requester_id=:actor",
        "recolector": """EXISTS (SELECT 1 FROM request_assignments a WHERE a.request_id=r.id
                                 AND a.collector_id=:actor AND a.is_current)""",
        **dict.fromkeys(COORDINATORS, COORD_SCOPE),
    }
    if actor.role not in scopes:
        raise HTTPException(403, "forbidden")
    params = {"id": request_id, "actor": actor.id, "coord_flow": COORDINATORS.get(actor.role)}
    with engine().connect() as conn:
        row = conn.execute(text(f"""
            SELECT {FIELDS}, r.generator,r.contact_phone,r.address,r.preferred_time,r.observations
                 ,a.collector_id,u.full_name AS collector_name,s.scheduled_start,s.scheduled_end
            FROM pickup_requests r
            LEFT JOIN request_assignments a ON a.request_id=r.id AND a.is_current
            LEFT JOIN users u ON u.id=a.collector_id
            LEFT JOIN request_schedules s ON s.assignment_id=a.id AND s.is_current
            WHERE r.id=:id AND ({scopes[actor.role]})
        """), params).mappings().first()
        if row is None:
            raise HTTPException(404, "request_not_found")
        history = conn.execute(text("""
            SELECT to_status,changed_at,reason FROM request_status_history
            WHERE request_id=:id ORDER BY changed_at,id
        """), {"id": request_id}).mappings().all()
        return {**row, "history": history}

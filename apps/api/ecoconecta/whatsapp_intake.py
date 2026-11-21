"""Entrega autenticada de un aviso confirmado en el piloto."""
import hmac
import os
from typing import Annotated, Literal
from uuid import UUID, uuid5, NAMESPACE_URL

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text

from .db import engine

router = APIRouter()


class Pickup(BaseModel):
    flow: Literal["organico", "reciclable"]
    address: str = Field(min_length=1, max_length=250)
    materials: list[Annotated[str, Field(min_length=1, max_length=100)]] = Field(min_length=1, max_length=40)


class ConfirmedNotice(BaseModel):
    attempt: UUID
    message_id: str = Field(min_length=1, max_length=256)
    phone: str = Field(pattern=r"^\+[1-9][0-9]{6,14}$")
    generator: Literal["hogar", "unidad_productiva"] | None = None
    preference: str = Field(min_length=1, max_length=150)
    pickups: list[Pickup] = Field(min_length=1, max_length=20)


@router.post("/integrations/whatsapp/confirmed")
def confirmed(body: ConfirmedNotice, authorization: Annotated[str, Header()] = ""):
    token = os.getenv("WHATSAPP_BRIDGE_TOKEN")
    if not token or not hmac.compare_digest(authorization.encode(), ("Bearer " + token).encode()):
        raise HTTPException(403, "forbidden")
    with engine().begin() as db:
        actor = db.execute(text("""SELECT u.id,p.generator_type FROM users u
            JOIN requester_profiles p ON p.user_id=u.id
            WHERE u.phone=:phone AND u.role='solicitante' AND u.is_active AND u.is_pilot
            AND EXISTS (SELECT 1 FROM consents c WHERE c.user_id=u.id AND c.revoked_at IS NULL)
            FOR UPDATE OF u"""), {"phone": body.phone}).mappings().first()
        if not actor:
            raise HTTPException(409, "resident_registration_required")
        zone = db.scalar(text("SELECT id FROM zones WHERE code=:code AND is_active FOR SHARE"),
                         {"code": os.getenv("WHATSAPP_PILOT_ZONE_CODE")})
        if not zone:
            raise HTTPException(409, "pilot_zone_missing")
        codes = []
        for index, pickup in enumerate(body.pickups):
            event = f"pilot:{actor['id']}:{body.attempt}:{index}"
            code = "SR-" + uuid5(NAMESPACE_URL, event).hex
            msg = f"{body.message_id}:{index}"
            existing = db.execute(text("""SELECT r.code FROM whatsapp_messages w
                JOIN pickup_requests r ON r.id=w.request_id WHERE w.provider='whatsapp_cloud'
                AND w.user_id=:uid AND (w.provider_message_id=:msg OR r.code=:code)"""),
                {"uid": actor["id"], "msg": msg, "code": code}).scalar_one_or_none()
            if existing:
                codes.append(existing)
                continue
            collective = db.scalar(text("SELECT id FROM collectives WHERE flow=:flow"), {"flow": pickup.flow})
            if not collective:
                raise HTTPException(409, "flow_unconfigured")
            rid = db.scalar(text("""INSERT INTO pickup_requests
                (code,requester_id,collective_id,flow,zone_id,generator,contact_phone,address,
                 preferred_time,observations,source_channel)
                VALUES (:code,:uid,:collective,:flow,:zone,:generator,:phone,:address,:preference,:note,'whatsapp')
                RETURNING id"""), dict(code=code,uid=actor["id"],collective=collective,flow=pickup.flow,
                    zone=zone,generator=body.generator or actor["generator_type"],phone=body.phone,
                    address=pickup.address,preference=body.preference,note=", ".join(pickup.materials)))
            db.execute(text("INSERT INTO request_status_history(request_id,to_status,changed_by) VALUES (:rid,'recibida',:uid)"),
                       {"rid":rid,"uid":actor["id"]})
            db.execute(text("""INSERT INTO whatsapp_messages(provider,provider_message_id,user_id,request_id,direction,delivery_status)
                VALUES ('whatsapp_cloud',:msg,:uid,:rid,'entrante','processed')"""),
                       {"msg":msg,"uid":actor["id"],"rid":rid,"event":event})
            codes.append(code)
        return {"codes": codes}


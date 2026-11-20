from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import Field, StrictBool
from sqlalchemy import text

from . import operation_views as v
from .auth import Admin
from .db import engine
from .operations import Input, Name, Slot
from .requests import Flow

router = APIRouter(prefix="/admin", tags=["Configuración operativa"])


class Zone(Input):
    code: Name
    name: Name
    is_active: StrictBool = True


class Material(Input):
    name: Name
    flow: Flow
    is_active: StrictBool = True


class Group(Input):
    name: Name


def configure(sql, params, actor, entity):
    with engine().begin() as db:
        row = db.execute(text(sql), params).mappings().first()
        if not row:
            raise HTTPException(409, "configuration_conflict")
        db.execute(
            text("""INSERT INTO audit_log(actor_id,action,entity,entity_id)
            VALUES (:actor,'configuration.saved',:entity,:id)"""),
            {"actor": actor.id, "entity": entity, "id": row["id"]},
        )
        return row


@router.put("/zones", response_model=v.ConfiguredZone)
def configure_zone(body: Zone, actor: Admin):
    return configure(
        """INSERT INTO zones(code,name,is_active) VALUES (:code,:name,:is_active)
        ON CONFLICT(code) DO UPDATE SET name=excluded.name,is_active=excluded.is_active RETURNING *""",
        body.model_dump(),
        actor,
        "zones",
    )


@router.put("/materials", response_model=v.ConfiguredMaterial)
def configure_material(body: Material, actor: Admin):
    return configure(
        """INSERT INTO waste_types(name,flow,unit,is_active) VALUES (:name,:flow,'kg',:is_active)
        ON CONFLICT(name) DO UPDATE SET is_active=excluded.is_active WHERE waste_types.flow=excluded.flow
        AND waste_types.unit='kg' RETURNING id,name,flow,unit,is_active""",
        body.model_dump(),
        actor,
        "waste_types",
    )


@router.put("/collectives/{flow}", response_model=v.ConfiguredGroup)
def configure_collective(flow: Flow, body: Group, actor: Admin):
    from sqlalchemy.exc import IntegrityError

    try:
        return configure(
            """INSERT INTO collectives(name,flow) VALUES (:name,:flow) ON CONFLICT(flow)
            DO UPDATE SET name=excluded.name RETURNING *""",
            {"name": body.name, "flow": flow},
            actor,
            "collectives",
        )
    except IntegrityError as exc:
        raise HTTPException(409, "collective_name_taken") from exc


class PublishedSlot(Slot):
    flow: Flow
    zone_id: UUID
    generator: str = Field(pattern="^(hogar|unidad_productiva)$")


@router.post("/schedules", response_model=v.ID, status_code=201)
def publish_schedule(body: PublishedSlot, actor: Admin):
    return configure(
        """INSERT INTO collection_schedules(collective_id,zone_id,generator,weekday,starts_at,
        ends_at,valid_from,valid_until) SELECT c.id,z.id,:generator,:weekday,:starts_at,:ends_at,:valid_from,
        :valid_until FROM collectives c,zones z WHERE c.flow=:flow AND z.id=:zone_id AND z.is_active
        RETURNING *""",
        body.model_dump(),
        actor,
        "collection_schedules",
    )

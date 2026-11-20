from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import Field
from sqlalchemy import text

from . import operation_views as v
from .auth import Actor
from .db import engine
from .operations import Input, Name

router = APIRouter(tags=["Huerta"])
ZONES = """SELECT z.zone_id FROM coordinator_zones z JOIN collective_members m ON m.id=z.member_id
    JOIN collectives c ON c.id=m.collective_id WHERE m.user_id=:actor AND m.member_role='coordinador' AND c.flow='organico'"""


class Need(Input):
    zone_id: UUID
    name: Name
    unit: Name
    quantity: Decimal = Field(ge=0, max_digits=14, decimal_places=4)


def require_garden(actor):
    if actor.role != "coordinador_huerteros":
        raise HTTPException(403, "forbidden")


@router.get("/garden/needs", response_model=list[v.GardenNeed])
def needs(actor: Actor):
    require_garden(actor)
    with engine().connect() as db:
        return (
            db.execute(
                text(
                    f"SELECT * FROM garden_needs WHERE zone_id IN ({ZONES}) ORDER BY zone_id,name,unit"
                ),
                {"actor": actor.id},
            )
            .mappings()
            .all()
        )


@router.put("/garden/needs", response_model=v.GardenNeed)
def record_need(body: Need, actor: Actor):
    require_garden(actor)
    with engine().begin() as db:
        row = (
            db.execute(
                text(f"""INSERT INTO garden_needs(zone_id,name,unit,quantity)
            SELECT :zone_id,:name,:unit,:quantity WHERE :zone_id IN ({ZONES})
            ON CONFLICT(zone_id,name,unit) DO UPDATE SET quantity=excluded.quantity,updated_at=now()
            RETURNING *"""),
                {**body.model_dump(), "actor": actor.id},
            )
            .mappings()
            .first()
        )
        if not row:
            raise HTTPException(404, "zone_not_found")
        return row

from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field
from sqlalchemy import text

from .auth import Actor, Identity
from .db import engine

router = APIRouter(tags=["Puntos"])
Rate = Annotated[Decimal, Field(gt=0, max_digits=12, decimal_places=6)]


def require_admin(actor: Actor):
    if actor.role != "administrador":
        raise HTTPException(403, "forbidden")
    return actor


Admin = Annotated[Identity, Depends(require_admin)]


class RuleInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    points_per_kg: Rate
    valid_from: AwareDatetime | None = None


class OrganicRuleInput(RuleInput):
    points_per_kg: Rate = Decimal("10")


class Rule(BaseModel):
    id: UUID
    waste_type_id: UUID
    version: int
    points_per_kg: Decimal
    valid_from: AwareDatetime
    valid_to: AwareDatetime | None


class Balance(BaseModel):
    balance: Decimal


RULE_FIELDS = "id,waste_type_id,version,points_per_unit AS points_per_kg,valid_from,valid_to"


@router.get("/points/rules", response_model=list[Rule])
def list_rules(actor: Admin):
    with engine().connect() as conn:
        return conn.execute(text(f"""
            SELECT {RULE_FIELDS} FROM points_rules
            WHERE validated_by_fsd AND approved_by IS NOT NULL
            ORDER BY waste_type_id,valid_from DESC,version DESC
        """)).mappings().all()


def publish(conn, material_id, body, actor):
    params = {"material": material_id, "rate": body.points_per_kg, "start": body.valid_from, "actor": actor.id}
    rule = conn.execute(text(f"""
        INSERT INTO points_rules(waste_type_id,points_per_unit,version,base_unit,
                                  description,valid_from,validated_by_fsd,created_by,approved_by)
        SELECT :material,:rate,COALESCE(MAX(version),0)+1,'kg',
               'Tarifa por kilo publicada por administración',COALESCE(:start,now()),true,:actor,:actor
        FROM points_rules WHERE waste_type_id=:material
        RETURNING {RULE_FIELDS}
    """), params).mappings().one()
    conn.execute(text("""
        INSERT INTO audit_log(actor_id,action,entity,entity_id)
        VALUES (:actor,'points.rule_published','points_rules',:id)
    """), {"actor": actor.id, "id": rule["id"]})
    return rule


@router.post("/admin/points/rules/organic", response_model=list[Rule], status_code=201)
def set_organic_rate(body: OrganicRuleInput, actor: Admin):
    with engine().begin() as conn:
        materials = conn.scalars(text("""
            SELECT id FROM waste_types WHERE flow='organico' AND unit='kg' AND is_active
            ORDER BY id FOR NO KEY UPDATE
        """)).all()
        if not materials:
            raise HTTPException(409, "no_organic_materials")
        return [publish(conn, material, body, actor) for material in materials]


@router.post("/admin/points/rules/{material_id}", response_model=Rule, status_code=201)
def set_recycling_rate(material_id: UUID, body: RuleInput, actor: Admin):
    with engine().begin() as conn:
        material = conn.scalar(text("""
            SELECT id FROM waste_types WHERE id=:id AND flow='reciclable' AND unit='kg' AND is_active
            FOR NO KEY UPDATE
        """), {"id": material_id})
        if material is None:
            raise HTTPException(422, "invalid_material")
        return publish(conn, material, body, actor)


@router.get("/users/me/points", response_model=Balance)
def balance(actor: Actor):
    with engine().connect() as conn:
        earned = conn.scalar(text("""
            SELECT COALESCE(SUM(points),0) FROM points_ledger WHERE user_id=:actor
        """), {"actor": actor.id})
    return Balance(balance=earned)

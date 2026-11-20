from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import AwareDatetime, Field
from sqlalchemy import text

from . import operation_views as v
from .auth import Actor, Admin
from .db import engine
from .operations import Input, Limit, Name, Offset
from .requests import COORD_SCOPE, COORDINATORS

router = APIRouter(tags=["Reportes"])


class Price(Input):
    valid_from: AwareDatetime
    cop_per_kg: Decimal = Field(ge=0, max_digits=14, decimal_places=2)
    source: Name


@router.post(
    "/admin/purchase-rates/{material_id}",
    response_model=v.PurchaseRate,
    status_code=201,
)
def publish_price(material_id: UUID, body: Price, actor: Admin):
    with engine().begin() as db:
        row = (
            db.execute(
                text("""INSERT INTO purchase_rates(material_id,valid_from,cop_per_kg,source,created_by)
            SELECT id,:valid_from,:cop_per_kg,:source,:actor FROM waste_types WHERE id=:id AND unit='kg'
            AND flow='reciclable' ON CONFLICT(material_id,valid_from) DO NOTHING RETURNING *"""),
                {**body.model_dump(), "id": material_id, "actor": actor.id},
            )
            .mappings()
            .first()
        )
        if not row:
            raise HTTPException(409, "purchase_rate_conflict")
        return row


@router.get("/coordinator/reports/purchase-value", response_model=list[v.PurchaseValue])
def purchase_value(actor: Actor, start: AwareDatetime, end: AwareDatetime):
    if actor.role not in COORDINATORS:
        raise HTTPException(403, "forbidden")
    if end <= start:
        raise HTTPException(422, "invalid_period")
    with engine().connect() as db:
        return (
            db.execute(
                text(f"""SELECT r.collective_id,i.waste_type_id,sum(i.quantity) AS kg,
            CASE WHEN count(price.id)=count(*) THEN sum(i.quantity*price.cop_per_kg) END AS estimated_cop,
            count(*)-count(price.id) AS missing_prices FROM pickup_requests r JOIN collections c ON c.request_id=r.id
            JOIN collection_items i ON i.collection_id=c.id LEFT JOIN LATERAL (
                SELECT p.id,p.cop_per_kg FROM purchase_rates p WHERE p.material_id=i.waste_type_id
                AND p.valid_from<=c.collected_at ORDER BY p.valid_from DESC LIMIT 1
            ) price ON true WHERE {COORD_SCOPE} AND r.flow='reciclable' AND i.unit='kg' AND c.confirmed_at IS NOT NULL
            AND c.collected_at>=:start AND c.collected_at<:end GROUP BY r.collective_id,i.waste_type_id
            ORDER BY r.collective_id,i.waste_type_id"""),
                {
                    "actor": actor.id,
                    "coord_flow": COORDINATORS[actor.role],
                    "start": start,
                    "end": end,
                },
            )
            .mappings()
            .all()
        )


@router.get("/users/me/points/ledger", response_model=list[v.Movement])
def ledger(actor: Actor, limit: Limit = 50, offset: Offset = 0):
    with engine().connect() as db:
        return (
            db.execute(
                text("""SELECT id,collection_id,reason,points,created_at FROM points_ledger
            WHERE user_id=:actor ORDER BY created_at DESC,id LIMIT :limit OFFSET :offset"""),
                {"actor": actor.id, "limit": limit, "offset": offset},
            )
            .mappings()
            .all()
        )


@router.get("/coordinator/reports/requests", response_model=list[v.RequestCount])
def request_counts(
    actor: Actor, start: AwareDatetime, end: AwareDatetime, zone_id: UUID | None = None
):
    if actor.role not in COORDINATORS:
        raise HTTPException(403, "forbidden")
    if end <= start:
        raise HTTPException(422, "invalid_period")
    with engine().connect() as db:
        return (
            db.execute(
                text(f"""SELECT r.flow,r.status,count(*) AS requests
            FROM pickup_requests r WHERE {COORD_SCOPE} AND r.created_at>=:start AND r.created_at<:end
            AND (cast(:zone AS uuid) IS NULL OR r.zone_id=:zone)
            GROUP BY r.flow,r.status ORDER BY r.flow,r.status"""),
                {
                    "actor": actor.id,
                    "coord_flow": COORDINATORS[actor.role],
                    "start": start,
                    "end": end,
                    "zone": zone_id,
                },
            )
            .mappings()
            .all()
        )

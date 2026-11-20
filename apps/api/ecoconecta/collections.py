from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import text

from .auth import Actor, Identity
from .db import engine
from .requests import COORDINATORS, FIELDS, Flow, Summary
from .scheduling import scoped_request, transition

router = APIRouter(tags=["Recolecciones"])


def require_collector(actor: Actor):
    if actor.role != "recolector":
        raise HTTPException(403, "forbidden")
    return actor


Collector = Annotated[Identity, Depends(require_collector)]


class Material(BaseModel):
    id: UUID
    name: str
    flow: Flow
    unit: str


class ItemInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    waste_type_id: UUID
    quantity: Decimal = Field(gt=0, max_digits=14, decimal_places=4)


class Item(BaseModel):
    id: UUID
    waste_type_id: UUID
    quantity: Decimal
    unit: str


class Collection(BaseModel):
    id: UUID
    request_id: UUID
    collected_at: datetime
    confirmed_at: datetime | None
    items: list[Item]


class ConfirmInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    items: list[ItemInput] = Field(min_length=1, max_length=100)


class ConfirmedCollection(Collection):
    points_awarded: Decimal


def coordinator_collection(conn, request_id, actor, *, lock):
    request = scoped_request(conn, request_id, actor, lock=lock)
    assigned = conn.execute(text("""
        SELECT a.id,a.collector_id FROM request_assignments a
        WHERE a.request_id=:id AND a.is_current
    """), {"id": request_id}).mappings().first()
    if assigned is None:
        raise HTTPException(404, "collection_not_found")
    return request, read_collection(conn, request_id, assigned["collector_id"], assigned["id"])


@router.get("/public/materials", response_model=list[Material])
def materials(flow: Flow):
    with engine().connect() as conn:
        return conn.execute(text("""
            SELECT id,name,flow,unit FROM waste_types WHERE flow=:flow AND is_active ORDER BY name,id
        """), {"flow": flow}).mappings().all()


@router.get("/collector/requests", response_model=list[Summary])
def assigned_requests(actor: Collector, limit: Annotated[int, Query(ge=1, le=100)] = 30,
                      offset: Annotated[int, Query(ge=0)] = 0):
    with engine().connect() as conn:
        return conn.execute(text(f"""
            SELECT {FIELDS} FROM pickup_requests r
            JOIN request_assignments a ON a.request_id=r.id AND a.is_current
            WHERE a.collector_id=:actor
            ORDER BY r.created_at DESC,r.id LIMIT :limit OFFSET :offset
        """), {"actor": actor.id, "limit": limit, "offset": offset}).mappings().all()


def read_collection(conn, request_id, collector_id, assignment_id):
    row = conn.execute(text("""
        SELECT id,request_id,collected_at,confirmed_at FROM collections
        WHERE request_id=:request AND collector_id=:collector AND assignment_id=:assignment
    """), {"request": request_id, "collector": collector_id, "assignment": assignment_id}).mappings().first()
    if row is None:
        raise HTTPException(404, "collection_not_found")
    items = conn.execute(text("""
        SELECT id,waste_type_id,quantity,unit FROM collection_items WHERE collection_id=:id ORDER BY id
    """), {"id": row["id"]}).mappings().all()
    return {**row, "items": items}


def assignment_for(conn, request_id, actor, *, lock=False):
    row = conn.execute(text("""
        SELECT a.id,r.status FROM pickup_requests r
        JOIN request_assignments a ON a.request_id=r.id AND a.is_current
        WHERE r.id=:rid AND a.collector_id=:actor
    """ + (" FOR UPDATE OF r,a" if lock else "")), {"rid": request_id, "actor": actor.id}).mappings().first()
    if row is None:
        raise HTTPException(404, "request_not_found")
    return row


@router.get("/requests/{request_id}/collection", response_model=Collection)
def get_collection(request_id: UUID, actor: Collector):
    with engine().connect() as conn:
        assignment = assignment_for(conn, request_id, actor)
        return read_collection(conn, request_id, actor.id, assignment["id"])


@router.post("/requests/{request_id}/collection", response_model=Collection, status_code=201,
             responses={200: {"model": Collection}})
def open_collection(request_id: UUID, actor: Collector, response: Response):
    with engine().begin() as conn:
        assignment = assignment_for(conn, request_id, actor, lock=True)
        if assignment["status"] != "programada":
            raise HTTPException(409, "invalid_transition")
        created = conn.scalar(text("""
            INSERT INTO collections(request_id,collector_id,assignment_id) VALUES (:rid,:actor,:assignment)
            ON CONFLICT (request_id) DO NOTHING RETURNING id
        """), {"rid": request_id, "actor": actor.id, "assignment": assignment["id"]})
        if created is None:
            response.status_code = 200
        return read_collection(conn, request_id, actor.id, assignment["id"])


@router.post("/collections/{collection_id}/items", response_model=Item, status_code=201,
             responses={200: {"model": Item}})
def record_item(collection_id: UUID, body: ItemInput, actor: Collector, response: Response):
    with engine().begin() as conn:
        row = conn.execute(text("""
            SELECT r.flow,r.status,c.confirmed_at FROM collections c
            JOIN pickup_requests r ON r.id=c.request_id
            JOIN request_assignments a ON a.id=c.assignment_id AND a.is_current
            WHERE c.id=:id AND c.collector_id=:actor AND a.collector_id=:actor
            FOR UPDATE OF r
        """), {"id": collection_id, "actor": actor.id}).mappings().first()
        if row is None:
            raise HTTPException(404, "collection_not_found")
        if row["confirmed_at"] or row["status"] != "programada":
            raise HTTPException(409, "collection_not_editable")
        params = {"id": collection_id, **body.model_dump()}
        previous = conn.execute(text("""
            SELECT id,waste_type_id,quantity,unit FROM collection_items
            WHERE collection_id=:id AND waste_type_id=:waste_type_id
        """), params).mappings().first()
        if previous:
            if previous["quantity"] != body.quantity:
                raise HTTPException(409, "material_already_recorded")
            response.status_code = 200
            return previous
        unit = conn.scalar(text("""
            SELECT unit FROM waste_types WHERE id=:waste_type_id AND flow=:flow AND is_active FOR SHARE
        """), {**params, "flow": row["flow"]})
        if unit is None:
            raise HTTPException(422, "invalid_material")
        return conn.execute(text("""
            INSERT INTO collection_items(collection_id,waste_type_id,quantity,unit)
            VALUES (:id,:waste_type_id,:quantity,:unit) RETURNING id,waste_type_id,quantity,unit
        """), {**params, "unit": unit}).mappings().one()


@router.get("/coordinator/requests/{request_id}/collection", response_model=Collection)
def collection_for_review(request_id: UUID, actor: Actor):
    with engine().connect() as conn:
        _, collection = coordinator_collection(conn, request_id, actor, lock=False)
        return collection


def verified_rates(conn, collection, flow, weights):
    rates = conn.execute(text("""
        SELECT w.id AS material,rule.id,rule.points_per_unit
        FROM waste_types w
        LEFT JOIN LATERAL (
            SELECT id,points_per_unit FROM points_rules p
            WHERE p.waste_type_id=w.id AND p.base_unit='kg'
              AND p.validated_by_fsd AND p.approved_by IS NOT NULL
              AND p.valid_from<=:collected_at AND (p.valid_to IS NULL OR p.valid_to>:collected_at)
            ORDER BY p.valid_from DESC,p.version DESC LIMIT 1
        ) rule ON true
        WHERE w.id=ANY(:materials) AND w.flow=:flow AND w.unit='kg' AND w.is_active
        ORDER BY w.id FOR SHARE OF w
    """), {"materials": list(weights), "flow": flow, "collected_at": collection["collected_at"]}).mappings().all()
    if len(rates) != len(weights):
        raise HTTPException(422, "invalid_material")
    if any(rate["id"] is None for rate in rates):
        raise HTTPException(409, "points_rule_missing")
    return rates


@router.post("/collections/{collection_id}/confirm", response_model=ConfirmedCollection)
def confirm_collection(collection_id: UUID, body: ConfirmInput, actor: Actor):
    if actor.role not in COORDINATORS:
        raise HTTPException(403, "forbidden")
    weights = {item.waste_type_id: item.quantity for item in body.items}
    if len(weights) != len(body.items):
        raise HTTPException(422, "duplicate_material")
    with engine().begin() as conn:
        request_id = conn.scalar(text("SELECT request_id FROM collections WHERE id=:id"), {"id": collection_id})
        if request_id is None:
            raise HTTPException(404, "collection_not_found")
        request, collection = coordinator_collection(conn, request_id, actor, lock=True)
        saved = {item["waste_type_id"]: item["quantity"] for item in collection["items"]}
        if collection["confirmed_at"] is not None:
            if saved != weights:
                raise HTTPException(409, "collection_not_editable")
            total = conn.scalar(text("""
                SELECT COALESCE(SUM(points),0) FROM points_ledger
                WHERE collection_id=:id AND reason='recoleccion'
            """), {"id": collection_id})
            return {**collection, "points_awarded": total}
        if request["status"] != "programada":
            raise HTTPException(409, "invalid_transition")
        if saved.keys() - weights.keys():
            raise HTTPException(422, "missing_recorded_material")

        rates = verified_rates(conn, collection, request["flow"], weights)
        credits = []
        for rate in rates:
            material = rate["material"]
            weight = weights[material]
            points = (weight * rate["points_per_unit"]).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
            if points <= 0:
                raise HTTPException(409, "points_below_precision")
            item_id = conn.scalar(text("""
                INSERT INTO collection_items(collection_id,waste_type_id,quantity,unit)
                VALUES (:id,:material,:weight,'kg')
                ON CONFLICT (collection_id,waste_type_id) DO UPDATE SET quantity=EXCLUDED.quantity
                RETURNING id
            """), {"id": collection_id, "material": material, "weight": weight})
            credits.append({"rule": rate["id"], "item": item_id, "weight": weight, "points": points})

        # The ledger trigger requires verification metadata. A failed credit rolls it back.
        conn.execute(text("""
            UPDATE collections SET confirmed_at=now(),confirmed_by=:actor,confirmation_key=:key
            WHERE id=:id
        """), {"id": collection_id, "actor": actor.id, "key": uuid4()})
        conn.execute(text("""
            INSERT INTO points_ledger(user_id,collection_id,rule_id,collection_item_id,base_quantity,
                                      base_unit,reason,points,idempotency_key,created_by)
            SELECT requester_id,:id,:rule,:item,:weight,'kg','recoleccion',:points,gen_random_uuid(),:actor
            FROM pickup_requests WHERE id=:request_id
        """), [{**credit, "id": collection_id, "actor": actor.id, "request_id": request_id}
                for credit in credits])
        transition(conn, request, actor, "recolectada")
        _, closed = coordinator_collection(conn, request_id, actor, lock=False)
        return {**closed, "points_awarded": sum(credit["points"] for credit in credits)}

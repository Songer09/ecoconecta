from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import Field
from sqlalchemy import text

from . import operation_views as v
from .auth import Actor, Admin
from .db import engine
from .operations import Input, Limit, Name, Offset, resident

router = APIRouter(tags=["Canjes"])


class Reward(Input):
    name: Name
    price: int = Field(gt=0, le=1000000000)
    stock: int = Field(ge=0, le=1000000000)


class Redeem(Input):
    reward_id: UUID
    quantity: int = Field(gt=0, le=10000)
    idempotency_key: UUID


@router.get("/rewards", response_model=list[v.RewardView])
def catalog(actor: Actor, limit: Limit = 50, offset: Offset = 0):
    with engine().connect() as db:
        return (
            db.execute(
                text(
                    "SELECT * FROM rewards ORDER BY name,id LIMIT :limit OFFSET :offset"
                ),
                {"limit": limit, "offset": offset},
            )
            .mappings()
            .all()
        )


@router.post("/admin/rewards", response_model=v.RewardView, status_code=201)
def create_reward(body: Reward, actor: Admin):
    with engine().begin() as db:
        reward = (
            db.execute(
                text("""INSERT INTO rewards(name,price,stock) VALUES (:name,:price,:stock)
            ON CONFLICT(name) DO NOTHING RETURNING *"""),
                body.model_dump(),
            )
            .mappings()
            .first()
        )
        if not reward:
            raise HTTPException(409, "reward_exists")
        db.execute(
            text("""INSERT INTO audit_log(actor_id,action,entity,entity_id)
            VALUES (:actor,'reward.created','rewards',:id)"""),
            {"actor": actor.id, "id": reward["id"]},
        )
        return reward


class Restock(Input):
    expected_stock: int = Field(ge=0, le=1000000000)
    stock: int = Field(ge=0, le=1000000000)


@router.put("/admin/rewards/{reward_id}/stock", response_model=v.RewardView)
def restock(reward_id: UUID, body: Restock, actor: Admin):
    with engine().begin() as db:
        row = (
            db.execute(
                text("""UPDATE rewards SET stock=:stock WHERE id=:id AND stock=:expected_stock
            RETURNING *"""),
                {"id": reward_id, **body.model_dump()},
            )
            .mappings()
            .first()
        )
        if not row:
            raise HTTPException(409, "stock_conflict")
        db.execute(
            text("""INSERT INTO audit_log(actor_id,action,entity,entity_id)
            VALUES (:actor,'reward.restocked','rewards',:id)"""),
            {"actor": actor.id, "id": reward_id},
        )
        return row


@router.get("/users/me/redemptions", response_model=list[v.Redemption])
def history(actor: Actor, limit: Limit = 30, offset: Offset = 0):
    resident(actor)
    with engine().connect() as db:
        return (
            db.execute(
                text("""SELECT * FROM redemptions WHERE user_id=:id
            ORDER BY created_at DESC,id LIMIT :limit OFFSET :offset"""),
                {"id": actor.id, "limit": limit, "offset": offset},
            )
            .mappings()
            .all()
        )


@router.post("/users/me/redemptions", response_model=v.Redemption)
def redeem(body: Redeem, actor: Actor):
    resident(actor)
    params = {**body.model_dump(), "actor": actor.id}
    with engine().begin() as db:
        db.execute(text("SELECT id FROM users WHERE id=:actor FOR UPDATE"), params)
        previous = (
            db.execute(
                text("""SELECT r.* FROM redemptions r JOIN points_ledger p ON p.id=r.id
            WHERE p.idempotency_key=:idempotency_key AND r.user_id=:actor"""),
                params,
            )
            .mappings()
            .first()
        )
        if previous:
            if (
                previous["reward_id"] != body.reward_id
                or previous["quantity"] != body.quantity
            ):
                raise HTTPException(409, "redemption_conflict")
            return previous
        reward = (
            db.execute(
                text("SELECT price,stock FROM rewards WHERE id=:reward_id FOR UPDATE"),
                params,
            )
            .mappings()
            .first()
        )
        if not reward or reward["stock"] < body.quantity:
            raise HTTPException(409, "stock_unavailable")
        params["cost"] = reward["price"] * body.quantity
        balance = db.scalar(
            text(
                "SELECT points_balance FROM requester_points_balances WHERE user_id=:actor"
            ),
            params,
        )
        if balance < params["cost"]:
            raise HTTPException(409, "insufficient_points")
        ledger_id = db.scalar(
            text("""INSERT INTO points_ledger(user_id,reason,points,idempotency_key,created_by)
            VALUES (:actor,'canje',-cast(:cost AS numeric),:idempotency_key,:actor)
            ON CONFLICT(idempotency_key) DO NOTHING RETURNING id"""),
            params,
        )
        if not ledger_id:
            raise HTTPException(409, "redemption_conflict")
        db.execute(
            text("UPDATE rewards SET stock=stock-:quantity WHERE id=:reward_id"), params
        )
        return (
            db.execute(
                text("""INSERT INTO redemptions(id,user_id,reward_id,quantity,cost)
            VALUES (:id,:actor,:reward_id,:quantity,:cost) RETURNING *"""),
                {**params, "id": ledger_id},
            )
            .mappings()
            .one()
        )

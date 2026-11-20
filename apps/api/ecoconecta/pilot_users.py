from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field, SecretStr, StrictBool
from sqlalchemy import text

from .auth import Admin, hasher
from .db import engine

router = APIRouter(prefix="/admin/users", tags=["Usuarios piloto"])
FIELDS = "id, full_name, role, is_active, is_pilot"


class PilotUser(BaseModel):
    id: UUID
    full_name: str
    role: str
    is_active: bool
    is_pilot: bool


class ResidentInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    full_name: str = Field(min_length=1, max_length=200, pattern=r"^\s*[^\s\x00][^\x00]*$")
    phone: str = Field(pattern=r"^\+[1-9][0-9]{6,14}$")
    password: SecretStr = Field(min_length=12, max_length=256)


class AccessInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    is_pilot: StrictBool


def audit(db, actor, user_id, action):
    db.execute(text("""
        INSERT INTO audit_log(actor_id, action, entity, entity_id)
        VALUES (:actor, :action, 'users', :id)
    """), {"actor": actor.id, "action": action, "id": user_id})


@router.get("", response_model=list[PilotUser])
def list_users(actor: Admin, limit: Annotated[int, Query(ge=1, le=100)] = 50,
               offset: Annotated[int, Query(ge=0)] = 0):
    with engine().connect() as db:
        return db.execute(text(f"SELECT {FIELDS} FROM users ORDER BY id LIMIT :limit OFFSET :offset"),
                          {"limit": limit, "offset": offset}).mappings().all()


@router.post("", response_model=PilotUser, status_code=201)
def create_resident(body: ResidentInput, actor: Admin):
    password_hash = hasher.hash(body.password.get_secret_value())
    with engine().begin() as db:
        user = db.execute(text(f"""
            INSERT INTO users(full_name, phone, role, password_hash, is_pilot)
            VALUES (:name, :phone, 'solicitante', :hash, true)
            ON CONFLICT (phone) DO NOTHING RETURNING {FIELDS}
        """), {"name": body.full_name.strip(), "phone": body.phone, "hash": password_hash}).mappings().first()
        if user is None:
            raise HTTPException(409, "phone_in_use")
        audit(db, actor, user["id"], "pilot.resident_created")
        return user


@router.put("/{user_id}/pilot-access", response_model=PilotUser)
def set_access(user_id: UUID, body: AccessInput, actor: Admin):
    with engine().begin() as db:
        user = db.execute(text(f"SELECT {FIELDS} FROM users WHERE id=:id FOR UPDATE"),
                          {"id": user_id}).mappings().first()
        if user is None:
            raise HTTPException(404, "user_not_found")
        if user["role"] == "administrador":
            raise HTTPException(403, "protected_account")
        if user["is_pilot"] == body.is_pilot:
            return user
        user = db.execute(text(f"""
            UPDATE users SET is_pilot=:enabled, updated_at=now() WHERE id=:id RETURNING {FIELDS}
        """), {"id": user_id, "enabled": body.is_pilot}).mappings().one()
        if not body.is_pilot:
            db.execute(text("UPDATE api_sessions SET revoked=true WHERE user_id=:id AND NOT revoked"),
                       {"id": user_id})
        audit(db, actor, user_id, "pilot.enabled" if body.is_pilot else "pilot.disabled")
        return user

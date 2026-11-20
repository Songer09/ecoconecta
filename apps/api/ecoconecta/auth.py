import hashlib
import secrets
from typing import Annotated
from uuid import UUID

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, InvalidHashError
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field, SecretStr
from sqlalchemy import text

from .db import engine

router = APIRouter(prefix="/auth", tags=["Autenticación"])
hasher = PasswordHasher()
dummy_hash = hasher.hash(secrets.token_urlsafe(32))
bearer = HTTPBearer(auto_error=False)


class Login(BaseModel):
    model_config = ConfigDict(extra="forbid")
    phone: str = Field(pattern=r"^\+[1-9][0-9]{6,14}$")
    password: SecretStr = Field(min_length=1, max_length=256)


class Identity(BaseModel):
    id: UUID
    role: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def token_digest(credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]):
    if credentials is None or len(credentials.credentials) > 128:
        raise HTTPException(401, "invalid_session")
    return digest(credentials.credentials)


SessionKey = Annotated[str, Depends(token_digest)]


def current_user(key: SessionKey) -> Identity:
    with engine().connect() as conn:
        user = conn.execute(text("""
            SELECT u.id, u.role FROM api_sessions s JOIN users u ON u.id=s.user_id
            WHERE s.token_digest=:key AND NOT s.revoked AND s.expires_at > now()
              AND u.is_active AND u.is_pilot
        """), {"key": key}).mappings().first()
    if user is None:
        raise HTTPException(401, "invalid_session")
    return Identity(**user)


Actor = Annotated[Identity, Depends(current_user)]


def require_admin(actor: Actor):
    if actor.role != "administrador":
        raise HTTPException(403, "forbidden")
    return actor


Admin = Annotated[Identity, Depends(require_admin)]


@router.post("/login", response_model=Token)
def login(body: Login, request: Request):
    # Count before password verification, including failed logins. One atomic window per peer.
    with engine().begin() as conn:
        count = conn.scalar(text("""
            INSERT INTO login_windows VALUES (:source, now(), 1)
            ON CONFLICT (source_digest) DO UPDATE SET
                attempts = CASE WHEN login_windows.started_at <= now()-interval '1 minute'
                    THEN 1 ELSE LEAST(login_windows.attempts+1, 21) END,
                started_at = CASE WHEN login_windows.started_at <= now()-interval '1 minute'
                    THEN now() ELSE login_windows.started_at END
            RETURNING attempts
        """), {"source": digest(request.client.host if request.client else "local")})
    if count > 20:
        raise HTTPException(429, "login_rate_limit", headers={"Retry-After": "60"})
    with engine().connect() as conn:
        user = conn.execute(text("""
            SELECT id, password_hash FROM users
            WHERE phone=:phone AND is_active AND is_pilot
        """), {"phone": body.phone}).mappings().first()
    stored = user["password_hash"] if user else None
    try:
        valid = hasher.verify(stored or dummy_hash, body.password.get_secret_value())
    except (VerificationError, InvalidHashError):
        valid = False
    if not stored or not valid:
        raise HTTPException(401, "invalid_credentials")
    token = secrets.token_urlsafe(32)
    with engine().begin() as conn:
        conn.execute(text("""
            INSERT INTO api_sessions(token_digest,user_id,expires_at)
            VALUES (:key,:uid,now()+interval '1 hour')
        """), {"key": digest(token), "uid": user["id"]})
    return Token(access_token=token)


@router.get("/me", response_model=Identity)
def me(actor: Actor):
    return actor


@router.post("/logout", status_code=204)
def logout(key: SessionKey, actor: Actor):
    with engine().begin() as conn:
        conn.execute(text("UPDATE api_sessions SET revoked=true WHERE token_digest=:key"), {"key": key})
    return Response(status_code=204)

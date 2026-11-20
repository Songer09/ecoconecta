from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text

from .auth import Actor
from .db import engine

router = APIRouter(tags=["Educación"])
Limit = Annotated[int, Query(ge=1, le=100)]
Offset = Annotated[int, Query(ge=0)]


class ModuleSummary(BaseModel):
    id: UUID
    title: str
    category: str
    flow: str | None


class Module(ModuleSummary):
    body: str


class Completion(BaseModel):
    module_id: UUID
    completed_at: datetime


class Progress(BaseModel):
    completed: int
    total: int
    percentage: int
    completions: list[Completion]


@router.get("/public/education", response_model=list[ModuleSummary])
def catalog(limit: Limit = 50, offset: Offset = 0):
    with engine().connect() as db:
        return db.execute(text("""
            SELECT id, title, category, flow FROM educational_content
            WHERE is_published ORDER BY created_at, id LIMIT :limit OFFSET :offset
        """), {"limit": limit, "offset": offset}).mappings().all()


@router.get("/public/education/{module_id}", response_model=Module)
def read_module(module_id: UUID):
    with engine().connect() as db:
        module = db.execute(text("""
            SELECT id, title, category, flow, body FROM educational_content
            WHERE id=:id AND is_published
        """), {"id": module_id}).mappings().first()
    if module is None:
        raise HTTPException(404, "module_not_found")
    return module


@router.put("/users/me/learning-progress/{module_id}", response_model=Completion)
def complete_module(module_id: UUID, actor: Actor):
    params = {"module": module_id, "user": actor.id}
    with engine().begin() as db:
        module = db.scalar(text("""
            SELECT id FROM educational_content WHERE id=:module AND is_published FOR SHARE
        """), params)
        if module is None:
            raise HTTPException(404, "module_not_found")
        db.execute(text("""
            INSERT INTO learning_completions (user_id, module_id) VALUES (:user, :module)
            ON CONFLICT (user_id, module_id) DO NOTHING
        """), params)
        return db.execute(text("""
            SELECT module_id, completed_at FROM learning_completions
            WHERE user_id=:user AND module_id=:module
        """), params).mappings().one()


@router.get("/users/me/learning-progress", response_model=Progress)
def profile_progress(actor: Actor, limit: Limit = 50, offset: Offset = 0):
    with engine().connect() as db:
        return db.execute(text("""
            WITH published AS (
                SELECT m.id, c.completed_at FROM educational_content m
                LEFT JOIN learning_completions c ON c.module_id=m.id AND c.user_id=:user
                WHERE m.is_published
            ), page AS (
                SELECT id AS module_id, completed_at FROM published WHERE completed_at IS NOT NULL
                ORDER BY completed_at DESC, id LIMIT :limit OFFSET :offset
            )
            SELECT count(completed_at) AS completed, count(*) AS total,
                coalesce(round(100.0 * count(completed_at) / nullif(count(*), 0)), 0) AS percentage,
                coalesce((SELECT json_agg(page ORDER BY completed_at DESC, module_id) FROM page), '[]') AS completions
            FROM published
        """), {"user": actor.id, "limit": limit, "offset": offset}).mappings().one()

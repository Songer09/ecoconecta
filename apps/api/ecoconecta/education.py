from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, StrictBool, field_validator
from sqlalchemy import text

from .auth import Actor, Admin
from .db import engine
from .requests import Flow

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


class DraftInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    title: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=20000)
    category: str = Field(min_length=1, max_length=100)
    flow: Flow | None = None

    @field_validator("title", "body", "category")
    @classmethod
    def postgres_text(cls, value: str) -> str:
        if "\x00" in value:
            raise ValueError("El texto contiene un carácter nulo.")
        return value


class ModuleUpdate(DraftInput):
    is_published: StrictBool
    expected_updated_at: AwareDatetime


class EditorialSummary(ModuleSummary):
    is_published: bool
    updated_at: datetime


class EditorialModule(EditorialSummary):
    body: str


EDITOR_FIELDS = "id, title, body, category, flow, is_published, updated_at"


def audit_edit(db, actor_id, module_id, action):
    db.execute(text("""
        INSERT INTO audit_log(actor_id, action, entity, entity_id)
        VALUES (:actor, :action, 'educational_content', :module)
    """), {"actor": actor_id, "module": module_id, "action": action})


@router.get("/admin/education", response_model=list[EditorialSummary])
def editorial_catalog(actor: Admin, limit: Limit = 50, offset: Offset = 0):
    with engine().connect() as db:
        return db.execute(text("""
            SELECT id, title, category, flow, is_published, updated_at FROM educational_content
            ORDER BY updated_at DESC, id LIMIT :limit OFFSET :offset
        """), {"limit": limit, "offset": offset}).mappings().all()


@router.get("/admin/education/{module_id}", response_model=EditorialModule)
def editorial_detail(module_id: UUID, actor: Admin):
    with engine().connect() as db:
        module = db.execute(text(f"SELECT {EDITOR_FIELDS} FROM educational_content WHERE id=:id"),
                            {"id": module_id}).mappings().first()
    if module is None:
        raise HTTPException(404, "module_not_found")
    return module


@router.post("/admin/education", response_model=EditorialModule, status_code=201)
def create_draft(body: DraftInput, actor: Admin):
    with engine().begin() as db:
        module = db.execute(text(f"""
            INSERT INTO educational_content(title, body, category, flow, created_by)
            VALUES (:title, :body, :category, :flow, :actor) RETURNING {EDITOR_FIELDS}
        """), {**body.model_dump(), "actor": actor.id}).mappings().one()
        audit_edit(db, actor.id, module["id"], "education.created")
        return module


@router.put("/admin/education/{module_id}", response_model=EditorialModule)
def update_module(module_id: UUID, body: ModuleUpdate, actor: Admin):
    with engine().begin() as db:
        previous = db.execute(text("""
            SELECT updated_at, is_published FROM educational_content WHERE id=:id FOR UPDATE
        """), {"id": module_id}).mappings().first()
        if previous is None:
            raise HTTPException(404, "module_not_found")
        if previous["updated_at"] != body.expected_updated_at:
            raise HTTPException(409, "module_version_conflict")
        module = db.execute(text(f"""
            UPDATE educational_content SET title=:title, body=:body, category=:category,
                flow=:flow, is_published=:is_published,
                updated_at=greatest(clock_timestamp(), updated_at + interval '1 microsecond')
            WHERE id=:id RETURNING {EDITOR_FIELDS}
        """), {**body.model_dump(), "id": module_id}).mappings().one()
        action = "education.edited"
        if previous["is_published"] != body.is_published:
            action = "education.published" if body.is_published else "education.withdrawn"
        audit_edit(db, actor.id, module_id, action)
        return module

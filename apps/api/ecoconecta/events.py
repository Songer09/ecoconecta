from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, StrictBool, model_validator
from sqlalchemy import text

from .auth import Admin
from .db import engine

router = APIRouter(tags=["Eventos"])
Limit = Annotated[int, Query(ge=1, le=100)]
Offset = Annotated[int, Query(ge=0)]
ShortText = Annotated[str, Field(min_length=1, max_length=200, pattern=r"^[^\x00]+$")]


class EventInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    title: ShortText
    organizer: ShortText
    location: ShortText
    description: str = Field(min_length=1, max_length=10000, pattern=r"^[^\x00]+$")
    starts_at: AwareDatetime
    ends_at: AwareDatetime

    @model_validator(mode="after")
    def validate_interval(self):
        if self.ends_at <= self.starts_at:
            raise ValueError("El fin debe ser posterior al inicio.")
        return self


class EventUpdate(EventInput):
    is_published: StrictBool
    expected_updated_at: AwareDatetime


class Event(EventInput):
    id: UUID


class EditorialEvent(Event):
    is_published: bool
    updated_at: AwareDatetime


PUBLIC = "id, title, description, organizer, location, starts_at, ends_at"
EDITORIAL = PUBLIC + ", is_published, updated_at"


@router.get("/public/events", response_model=list[Event])
def public_agenda(include_past: bool = False, limit: Limit = 50, offset: Offset = 0):
    with engine().connect() as db:
        return db.execute(text(f"""
            SELECT {PUBLIC} FROM community_events WHERE is_published
                AND (:include_past OR ends_at > now())
            ORDER BY starts_at, id LIMIT :limit OFFSET :offset
        """), {"include_past": include_past, "limit": limit, "offset": offset}).mappings().all()


@router.get("/public/events/{event_id}", response_model=Event)
def public_event(event_id: UUID):
    with engine().connect() as db:
        event = db.execute(text(f"""
            SELECT {PUBLIC} FROM community_events WHERE id=:id AND is_published
        """), {"id": event_id}).mappings().first()
    if event is None:
        raise HTTPException(404, "event_not_found")
    return event


@router.get("/admin/events", response_model=list[EditorialEvent])
def editorial_agenda(actor: Admin, limit: Limit = 50, offset: Offset = 0):
    with engine().connect() as db:
        return db.execute(text(f"""
            SELECT {EDITORIAL} FROM community_events
            ORDER BY updated_at DESC, id LIMIT :limit OFFSET :offset
        """), {"limit": limit, "offset": offset}).mappings().all()


@router.get("/admin/events/{event_id}", response_model=EditorialEvent)
def editorial_event(event_id: UUID, actor: Admin):
    with engine().connect() as db:
        event = db.execute(text(f"SELECT {EDITORIAL} FROM community_events WHERE id=:id"),
                           {"id": event_id}).mappings().first()
    if event is None:
        raise HTTPException(404, "event_not_found")
    return event


def audit_event(db, actor, event_id, action):
    db.execute(text("""
        INSERT INTO audit_log(actor_id, action, entity, entity_id)
        VALUES (:actor, :action, 'community_events', :id)
    """), {"actor": actor.id, "id": event_id, "action": action})


@router.post("/admin/events", status_code=201, response_model=EditorialEvent)
def create_event(body: EventInput, actor: Admin):
    with engine().begin() as db:
        event = db.execute(text(f"""
            INSERT INTO community_events(title, description, organizer, location, starts_at, ends_at, created_by)
            VALUES (:title, :description, :organizer, :location, :starts_at, :ends_at, :actor)
            RETURNING {EDITORIAL}
        """), {**body.model_dump(), "actor": actor.id}).mappings().one()
        audit_event(db, actor, event["id"], "event.created")
        return event


@router.put("/admin/events/{event_id}", response_model=EditorialEvent)
def update_event(event_id: UUID, body: EventUpdate, actor: Admin):
    with engine().begin() as db:
        current = db.execute(text("""
            SELECT updated_at, is_published FROM community_events WHERE id=:id FOR UPDATE
        """), {"id": event_id}).mappings().first()
        if current is None:
            raise HTTPException(404, "event_not_found")
        if current["updated_at"] != body.expected_updated_at:
            raise HTTPException(409, "event_version_conflict")
        event = db.execute(text(f"""
            UPDATE community_events SET title=:title, description=:description, organizer=:organizer,
                location=:location, starts_at=:starts_at, ends_at=:ends_at, is_published=:is_published,
                updated_at=greatest(clock_timestamp(), updated_at + interval '1 microsecond')
            WHERE id=:id RETURNING {EDITORIAL}
        """), {**body.model_dump(), "id": event_id}).mappings().one()
        action = "event.edited"
        if current["is_published"] != body.is_published:
            action = "event.published" if body.is_published else "event.withdrawn"
        audit_event(db, actor, event_id, action)
        return event

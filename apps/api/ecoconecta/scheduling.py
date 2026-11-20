from datetime import date, time
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import AwareDatetime, BaseModel, ConfigDict, model_validator
from sqlalchemy import text

from .auth import Actor
from .db import engine
from .requests import COORDINATORS, COORD_SCOPE, FIELDS, Summary

router = APIRouter(tags=["Coordinación"])


class AssignmentInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    collector_id: UUID


class ScheduleInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scheduled_start: AwareDatetime
    scheduled_end: AwareDatetime

    @model_validator(mode="after")
    def ordered(self):
        if self.scheduled_end <= self.scheduled_start:
            raise ValueError("El fin debe ser posterior al inicio")
        return self


class Availability(BaseModel):
    collector_id: UUID
    name: str
    weekday: int
    starts_at: time
    ends_at: time
    timezone: str
    valid_from: date
    valid_until: date | None


def scoped_request(conn, request_id, actor, *, lock):
    if actor.role not in COORDINATORS:
        raise HTTPException(403, "forbidden")
    row = conn.execute(text(
        f"SELECT {FIELDS},r.collective_id FROM pickup_requests r WHERE r.id=:id AND {COORD_SCOPE}"
        + (" FOR UPDATE OF r" if lock else "")
    ), {"id": request_id, "actor": actor.id, "coord_flow": COORDINATORS[actor.role]}).mappings().first()
    if row is None:
        raise HTTPException(404, "request_not_found")
    return row


def require_status(row, expected):
    if row["status"] != expected:
        raise HTTPException(409, "invalid_transition")


def transition(conn, row, actor, state):
    params = {"id": row["id"], "previous": row["status"], "state": state, "actor": actor.id}
    conn.execute(text("""
        INSERT INTO request_status_history(request_id,from_status,to_status,changed_by)
        VALUES (:id,:previous,:state,:actor)
    """), params)
    conn.execute(text("""
        INSERT INTO audit_log(actor_id,action,entity,entity_id)
        VALUES (:actor,:action,'pickup_requests',:id)
    """), {**params, "action": "request." + state})
    return conn.execute(text("UPDATE pickup_requests AS r SET status=:state, updated_at=now() "
                             "WHERE id=:id RETURNING " + FIELDS), params).mappings().one()


@router.post("/requests/{request_id}/review", response_model=Summary)
def review(request_id: UUID, actor: Actor):
    with engine().begin() as conn:
        row = scoped_request(conn, request_id, actor, lock=True)
        require_status(row, "recibida")
        return transition(conn, row, actor, "en_revision")


# Weekdays are ISO (Monday=1). Intersect the validity of both the slot and its coverage.
SLOTS = """
    SELECT u.id AS collector_id,u.full_name AS name,s.weekday,s.starts_at,s.ends_at,s.timezone,
           greatest(c.valid_from,s.valid_from) AS valid_from,
           least(c.valid_until,s.valid_until) AS valid_until
    FROM collective_members m JOIN users u ON u.id=m.user_id
    JOIN collector_zone_coverage c ON c.member_id=m.id
    JOIN availability_slots s ON s.coverage_id=c.id
    JOIN zones z ON z.id=c.zone_id
    WHERE m.collective_id=:collective_id AND z.id=:zone_id AND z.is_active
      AND m.member_role='recolector' AND m.is_available
      AND u.role='recolector' AND u.is_active AND u.is_pilot
"""
USABLE_SLOTS = f"""
    SELECT * FROM ({SLOTS}) slots
    WHERE valid_until IS NULL OR valid_until >= greatest(valid_from, (now() AT TIME ZONE timezone)::date)
"""


@router.get("/collectors/availability", response_model=list[Availability])
def availability(request_id: UUID, actor: Actor):
    with engine().connect() as conn:
        row = scoped_request(conn, request_id, actor, lock=False)
        return conn.execute(text(USABLE_SLOTS + " ORDER BY name,collector_id,weekday,starts_at"),
                            dict(row)).mappings().all()


@router.post("/requests/{request_id}/assignments", response_model=Summary, status_code=201)
def assign(request_id: UUID, body: AssignmentInput, actor: Actor):
    with engine().begin() as conn:
        row = scoped_request(conn, request_id, actor, lock=True)
        require_status(row, "en_revision")
        params = {**row, "collector_id": body.collector_id, "actor": actor.id}
        if not conn.scalar(text(f"SELECT 1 FROM ({USABLE_SLOTS}) v WHERE collector_id=:collector_id LIMIT 1"), params):
            raise HTTPException(409, "collector_unavailable")
        conn.execute(text("""
            INSERT INTO request_assignments(request_id,coordinator_id,collector_id)
            VALUES (:id,:actor,:collector_id)
        """), params)
        return transition(conn, row, actor, "asignada")


@router.post("/requests/{request_id}/schedule", response_model=Summary, status_code=201)
def schedule(request_id: UUID, body: ScheduleInput, actor: Actor):
    with engine().begin() as conn:
        row = scoped_request(conn, request_id, actor, lock=True)
        require_status(row, "asignada")
        assignment = conn.execute(text("""
            SELECT a.id AS assignment_id,u.id AS collector_id
            FROM request_assignments a JOIN users u ON u.id=a.collector_id
            WHERE a.request_id=:id AND a.is_current FOR NO KEY UPDATE OF u
        """), {"id": request_id}).mappings().one()
        # Serialize reservations for this person across all requests. Check in a fresh statement.
        params = {**row, **assignment, **body.model_dump(), "actor": actor.id}
        slot = conn.scalar(text(f"""
            SELECT timezone FROM ({SLOTS}) slots
            CROSS JOIN LATERAL (SELECT :scheduled_start AT TIME ZONE timezone AS local_start,
                                       :scheduled_end AT TIME ZONE timezone AS local_end) t
            WHERE collector_id=:collector_id AND :scheduled_start > clock_timestamp()
              AND local_start::date >= valid_from AND (valid_until IS NULL OR local_start::date <= valid_until)
              AND local_start::date=local_end::date AND extract(isodow FROM local_start)=weekday
              AND local_start::time >= starts_at AND local_end::time <= ends_at
            ORDER BY timezone LIMIT 1
        """), params)
        if slot is None:
            raise HTTPException(409, "outside_availability")
        if conn.scalar(text("""
            SELECT 1 FROM request_schedules s JOIN request_assignments a ON a.id=s.assignment_id
            JOIN pickup_requests r ON r.id=s.request_id
            WHERE s.is_current AND a.is_current AND r.status='programada' AND a.collector_id=:collector_id
              AND s.scheduled_start < :scheduled_end
              AND (s.scheduled_end > :scheduled_start OR
                   (s.scheduled_end IS NULL AND s.scheduled_start >= :scheduled_start))
            LIMIT 1
        """), params):
            raise HTTPException(409, "schedule_overlap")
        conn.execute(text("""
            INSERT INTO request_schedules(request_id,assignment_id,scheduled_start,scheduled_end,
                                          created_by,confirmed_by,timezone)
            VALUES (:id,:assignment_id,:scheduled_start,:scheduled_end,:actor,:actor,:timezone)
        """), {**params, "timezone": slot})
        return transition(conn, row, actor, "programada")

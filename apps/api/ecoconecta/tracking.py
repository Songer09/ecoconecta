import asyncio
import os
from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import APIRouter, HTTPException, Response
from pydantic import Field
from sqlalchemy import text

from . import operation_views as v
from .auth import Actor
from .collections import Collector
from .db import engine
from .operations import Input
from .requests import COORD_SCOPE, COORDINATORS

router = APIRouter(tags=["Ubicación en ruta"])


class Position(Input):
    request_id: UUID
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    accuracy_m: float = Field(gt=0, le=100000)


def require_enabled():
    if os.getenv("LIVE_TRACKING_ENABLED") != "1":
        raise HTTPException(409, "tracking_disabled")


def purge_expired():
    with engine().begin() as db:
        db.execute(
            text(
                "DELETE FROM live_positions WHERE updated_at <= now()-interval '5 minutes'"
            )
        )


@asynccontextmanager
async def lifespan(app):
    async def cleanup():
        from sqlalchemy.exc import OperationalError

        while True:
            try:
                await asyncio.to_thread(purge_expired)
            except OperationalError:
                pass
            await asyncio.sleep(15)

    task = asyncio.create_task(cleanup()) if os.getenv("DATABASE_URL") else None
    try:
        yield
    finally:
        if task is not None:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)


@router.put("/collector/location", status_code=204)
def share(body: Position, actor: Collector):
    require_enabled()
    with engine().begin() as db:
        row = db.scalar(
            text("""SELECT a.id FROM request_assignments a JOIN pickup_requests r ON r.id=a.request_id
            JOIN request_schedules s ON s.assignment_id=a.id AND s.is_current
            WHERE a.request_id=:request_id AND a.collector_id=:actor AND a.is_current AND r.status='programada'
            AND (s.scheduled_start AT TIME ZONE 'America/Bogota')::date=(now() AT TIME ZONE 'America/Bogota')::date
            FOR SHARE OF a,r,s"""),
            {**body.model_dump(), "actor": actor.id},
        )
        if not row:
            raise HTTPException(404, "active_stop_not_found")
        db.execute(
            text("""INSERT INTO live_positions(collector_id,assignment_id,latitude,longitude,accuracy_m)
            VALUES (:actor,:assignment,:latitude,:longitude,:accuracy_m) ON CONFLICT(collector_id) DO UPDATE SET
            assignment_id=excluded.assignment_id,latitude=excluded.latitude,longitude=excluded.longitude,
            accuracy_m=excluded.accuracy_m,updated_at=clock_timestamp()"""),
            {**body.model_dump(), "actor": actor.id, "assignment": row},
        )
    return Response(status_code=204)


@router.delete("/collector/location", status_code=204)
def stop(actor: Collector):
    with engine().begin() as db:
        db.execute(
            text("DELETE FROM live_positions WHERE collector_id=:actor"),
            {"actor": actor.id},
        )
    return Response(status_code=204)


@router.get("/coordinator/locations", response_model=list[v.LastPosition])
def positions(actor: Actor):
    require_enabled()
    if actor.role not in COORDINATORS:
        raise HTTPException(403, "forbidden")
    with engine().connect() as db:
        return (
            db.execute(
                text(f"""SELECT l.collector_id,r.zone_id,r.id AS request_id,l.latitude,l.longitude,
            l.accuracy_m,l.updated_at FROM live_positions l JOIN request_assignments a ON a.id=l.assignment_id
            JOIN pickup_requests r ON r.id=a.request_id JOIN users u ON u.id=l.collector_id
            WHERE a.is_current AND u.is_active AND u.is_pilot AND r.status='programada'
            AND l.updated_at>now()-interval '5 minutes' AND {COORD_SCOPE} ORDER BY l.collector_id"""),
                {"actor": actor.id, "coord_flow": COORDINATORS[actor.role]},
            )
            .mappings()
            .all()
        )


@router.post("/coordinator/requests/{request_id}/verify-location", status_code=204)
def verify_location(request_id: UUID, actor: Actor):
    require_enabled()
    if actor.role not in COORDINATORS:
        raise HTTPException(403, "forbidden")
    with engine().begin() as db:
        observation = db.scalar(text(f"""
            INSERT INTO audit_log(actor_id,action,entity,entity_id)
            SELECT :actor,'request.location_reviewed','pickup_requests',r.id
            FROM pickup_requests r JOIN request_assignments a ON a.request_id=r.id AND a.is_current
            JOIN live_positions l ON l.assignment_id=a.id JOIN users u ON u.id=l.collector_id
            WHERE r.id=:id AND r.status='programada' AND u.is_active AND u.is_pilot
            AND l.updated_at>now()-interval '5 minutes' AND {COORD_SCOPE} RETURNING id
        """), {"actor": actor.id, "coord_flow": COORDINATORS[actor.role], "id": request_id})
        if not observation:
            raise HTTPException(404, "active_position_not_found")
    return Response(status_code=204)

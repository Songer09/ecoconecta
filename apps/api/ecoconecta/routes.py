from datetime import date
from itertools import pairwise, permutations
from math import asin, cos, radians, sin, sqrt
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import Field
from sqlalchemy import text

from . import operation_views as v
from .auth import Actor
from .collections import Collector
from .db import engine
from .operations import Input
from .requests import COORD_SCOPE, COORDINATORS

router = APIRouter(tags=["Rutas"])
STOPS = """SELECT r.id,r.code,r.address,r.latitude,r.longitude,s.scheduled_start,s.scheduled_end,
    s.stop_order,a.collector_id FROM pickup_requests r
    JOIN request_assignments a ON a.request_id=r.id AND a.is_current
    JOIN request_schedules s ON s.assignment_id=a.id AND s.is_current
    WHERE r.status='programada' AND a.collector_id=:collector
    AND (s.scheduled_start AT TIME ZONE 'America/Bogota')::date=:day"""
ORDER = " ORDER BY s.stop_order NULLS LAST,s.scheduled_start,r.id"


class RouteOrder(Input):
    stops: list[UUID] = Field(min_length=1, max_length=500)


def distance(a, b):
    lat1, lon1, lat2, lon2 = map(
        radians,
        map(float, [a["latitude"], a["longitude"], b["latitude"], b["longitude"]]),
    )
    h = (
        sin((lat2 - lat1) / 2) ** 2
        + cos(lat1) * cos(lat2) * sin((lon2 - lon1) / 2) ** 2
    )
    return 2 * asin(sqrt(min(1, h)))


def scope(actor, day, collector, zone):
    if actor.role not in COORDINATORS:
        raise HTTPException(403, "forbidden")
    return {
        "actor": actor.id,
        "coord_flow": COORDINATORS[actor.role],
        "day": day,
        "collector": collector,
        "zone": zone,
    }


@router.get("/collector/route", response_model=list[v.Stop])
def my_route(day: date, actor: Collector):
    with engine().connect() as db:
        return (
            db.execute(
                text(
                    STOPS
                    + " ORDER BY r.zone_id,s.stop_order NULLS LAST,s.scheduled_start,r.id"
                ),
                {"day": day, "collector": actor.id},
            )
            .mappings()
            .all()
        )


@router.get("/coordinator/routes/{collector_id}", response_model=list[v.Stop])
def route(
    collector_id: UUID, day: date, zone_id: UUID, actor: Actor, suggest: bool = False
):
    params = scope(actor, day, collector_id, zone_id)
    with engine().connect() as db:
        rows = (
            db.execute(
                text(STOPS + f" AND r.zone_id=:zone AND {COORD_SCOPE}" + ORDER), params
            )
            .mappings()
            .all()
        )
    if not suggest:
        return rows
    located = [r for r in rows if r["latitude"] is not None]
    ordered = []
    if located:
        ordered.append(min(located, key=lambda r: (r["scheduled_start"], r["id"])))
        located.remove(ordered[0])
    if 1 < len(located) <= 7:
        stops = ordered + located
        distances = [[distance(a, b) for b in stops] for a in stops]
        def length(order):
            return sum(distances[i][j] for i,j in pairwise((0, *order)))
        best = min(permutations(range(1, len(stops))), key=length)
        ordered.extend(stops[i] for i in best)
        located.clear()
    while located:
        nearest = min(
            located,
            key=lambda r: (distance(ordered[-1], r), r["scheduled_start"], r["id"]),
        )
        ordered.append(nearest)
        located.remove(nearest)
    return ordered + [r for r in rows if r["latitude"] is None]


@router.put("/coordinator/routes/{collector_id}", response_model=RouteOrder)
def assign_route(
    collector_id: UUID, day: date, zone_id: UUID, body: RouteOrder, actor: Actor
):
    params = scope(actor, day, collector_id, zone_id)
    with engine().begin() as db:
        ids = (
            db.execute(
                text(
                    STOPS
                    + f" AND r.zone_id=:zone AND {COORD_SCOPE} ORDER BY r.id FOR UPDATE OF r,s"
                ),
                params,
            )
            .scalars()
            .all()
        )
        if not ids or len(ids) != len(body.stops) or set(ids) != set(body.stops):
            raise HTTPException(409, "route_stops_changed")
        db.execute(
            text(
                """UPDATE request_schedules SET stop_order=:position WHERE request_id=:id AND is_current"""
            ),
            [{"position": i, "id": rid} for i, rid in enumerate(body.stops, 1)],
        )
        db.execute(
            text("""INSERT INTO audit_log(actor_id,action,entity,entity_id)
            VALUES (:actor,'route.ordered','users',:collector)"""),
            params,
        )
    return body

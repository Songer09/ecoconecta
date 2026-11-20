from datetime import date, time
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    model_validator,
)
from sqlalchemy import text

from . import operation_views as v
from .auth import Actor, Admin, hasher
from .collections import Collector
from .db import engine
from .pilot_users import ResidentInput, audit
from .requests import COORD_SCOPE, COORDINATORS, FIELDS, Flow, Summary

router = APIRouter(tags=["Operación"])
Limit = Annotated[int, Query(ge=1, le=100)]
Offset = Annotated[int, Query(ge=0)]
Name = Annotated[str, Field(min_length=1, max_length=200, pattern=r"^[^\x00]+$")]


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Profile(Input):
    full_name: Name
    address: Name
    generator_type: Literal["hogar", "unidad_productiva"]
    neighborhood: Name | None = None
    business_name: Name | None = None


def resident(actor):
    if actor.role != "solicitante":
        raise HTTPException(403, "forbidden")


@router.get("/users/me/profile", response_model=v.ProfileView)
def profile(actor: Actor):
    resident(actor)
    with engine().connect() as db:
        return (
            db.execute(
                text("""
            SELECT u.full_name,p.address,p.generator_type,p.neighborhood,p.business_name
            FROM users u LEFT JOIN requester_profiles p ON p.user_id=u.id WHERE u.id=:id
        """),
                {"id": actor.id},
            )
            .mappings()
            .one()
        )


@router.put("/users/me/profile", response_model=Profile)
def save_profile(body: Profile, actor: Actor):
    resident(actor)
    params = {**body.model_dump(), "id": actor.id}
    with engine().begin() as db:
        db.execute(
            text("UPDATE users SET full_name=:full_name,updated_at=now() WHERE id=:id"),
            params,
        )
        db.execute(
            text("""
            INSERT INTO requester_profiles(user_id,address,generator_type,neighborhood,business_name)
            VALUES (:id,:address,:generator_type,:neighborhood,:business_name)
            ON CONFLICT (user_id) DO UPDATE SET address=excluded.address,generator_type=excluded.generator_type,
            neighborhood=excluded.neighborhood,business_name=excluded.business_name
        """),
            params,
        )
    return body


@router.get("/users/me/requests", response_model=list[Summary])
def my_requests(actor: Actor, limit: Limit = 30, offset: Offset = 0):
    resident(actor)
    with engine().connect() as db:
        return (
            db.execute(
                text(f"""SELECT {FIELDS} FROM pickup_requests r WHERE requester_id=:id
            ORDER BY created_at DESC,id LIMIT :limit OFFSET :offset"""),
                {"id": actor.id, "limit": limit, "offset": offset},
            )
            .mappings()
            .all()
        )


class Staff(ResidentInput):
    role: Literal["recolector", "coordinador_huerteros", "coordinador_recicladores"]
    flow: Flow
    zone_ids: list[UUID] = Field(min_length=1, max_length=100)
    valid_from: date


@router.post("/admin/staff", response_model=v.Membership, status_code=201)
def register_staff(body: Staff, actor: Admin):
    if COORDINATORS.get(body.role, body.flow) != body.flow:
        raise HTTPException(422, "role_flow_mismatch")
    with engine().begin() as db:
        collective = db.scalar(
            text("SELECT id FROM collectives WHERE flow=:flow"), {"flow": body.flow}
        )
        if not collective:
            raise HTTPException(409, "flow_unconfigured")
        zones = set(body.zone_ids)
        found = db.scalars(
            text("SELECT id FROM zones WHERE is_active AND id=ANY(:zones) FOR SHARE"),
            {"zones": list(zones)},
        ).all()
        if set(found) != zones:
            raise HTTPException(422, "inactive_zone")
        uid = db.scalar(
            text("""INSERT INTO users(full_name,phone,password_hash,role,is_pilot)
            VALUES (:name,:phone,:hash,:role,true) ON CONFLICT(phone) DO NOTHING RETURNING id"""),
            {
                "name": body.full_name.strip(),
                "phone": body.phone,
                "hash": hasher.hash(body.password.get_secret_value()),
                "role": body.role,
            },
        )
        if uid is None:
            raise HTTPException(409, "phone_in_use")
        collector = body.role == "recolector"
        mid = db.scalar(
            text("""INSERT INTO collective_members(user_id,collective_id,member_role)
            VALUES (:id,:collective,:role) RETURNING id"""),
            {
                "id": uid,
                "collective": collective,
                "role": "recolector" if collector else "coordinador",
            },
        )
        for zone in zones:
            if collector:
                db.execute(
                    text("""INSERT INTO collector_zone_coverage(member_id,zone_id,valid_from)
                    VALUES (:member,:zone,:start)"""),
                    {"member": mid, "zone": zone, "start": body.valid_from},
                )
            else:
                db.execute(
                    text("INSERT INTO coordinator_zones VALUES (:member,:zone)"),
                    {"member": mid, "zone": zone},
                )
        audit(db, actor, uid, "staff.created")
        return {"user_id": uid, "member_id": mid}


class Availability(Input):
    is_available: StrictBool


@router.get("/collector/availability", response_model=list[v.AvailableGroup])
def availability(actor: Collector):
    with engine().connect() as db:
        return (
            db.execute(
                text("""SELECT collective_id,is_available FROM collective_members
            WHERE user_id=:id AND member_role='recolector' ORDER BY collective_id"""),
                {"id": actor.id},
            )
            .mappings()
            .all()
        )


@router.put("/collector/availability/{collective_id}", response_model=Availability)
def set_availability(collective_id: UUID, body: Availability, actor: Collector):
    with engine().begin() as db:
        updated = db.scalar(
            text("""UPDATE collective_members SET is_available=:available WHERE user_id=:id
            AND collective_id=:group AND member_role='recolector' RETURNING id"""),
            {"available": body.is_available, "id": actor.id, "group": collective_id},
        )
        if not updated:
            raise HTTPException(404, "membership_not_found")
    return body


class Slot(Input):
    weekday: int = Field(ge=1, le=7)
    starts_at: time
    ends_at: time
    valid_from: date
    valid_until: date | None = None

    @model_validator(mode="after")
    def validate_interval(self):
        if (
            self.starts_at.tzinfo
            or self.ends_at.tzinfo
            or self.ends_at <= self.starts_at
        ):
            raise ValueError("Se requieren horas locales ordenadas.")
        if self.valid_until and self.valid_until < self.valid_from:
            raise ValueError("Verifica la vigencia.")
        return self


@router.get("/admin/staff/{user_id}/coverage", response_model=list[v.Coverage])
def coverage(user_id: UUID, actor: Admin):
    with engine().connect() as db:
        return (
            db.execute(
                text("""SELECT c.* FROM collector_zone_coverage c JOIN collective_members m
            ON m.id=c.member_id WHERE m.user_id=:id ORDER BY c.zone_id,c.valid_from"""),
                {"id": user_id},
            )
            .mappings()
            .all()
        )


@router.post(
    "/admin/coverage/{coverage_id}/slots", response_model=v.ID, status_code=201
)
def add_slot(coverage_id: UUID, body: Slot, actor: Admin):
    with engine().begin() as db:
        slot = db.scalar(
            text("""INSERT INTO availability_slots(coverage_id,weekday,starts_at,ends_at,valid_from,valid_until)
            SELECT id,:weekday,:starts_at,:ends_at,:valid_from,:valid_until FROM collector_zone_coverage
            WHERE id=:id RETURNING id"""),
            {**body.model_dump(), "id": coverage_id},
        )
        if not slot:
            raise HTTPException(404, "coverage_not_found")
        return {"id": slot}


@router.get("/coordinator/reports/materials", response_model=list[v.MaterialTotal])
def material_report(
    actor: Actor,
    start: AwareDatetime,
    end: AwareDatetime,
    zone_id: UUID | None = None,
    collector_id: UUID | None = None,
    limit: Limit = 100,
    offset: Offset = 0,
):
    if actor.role not in COORDINATORS:
        raise HTTPException(403, "forbidden")
    if end <= start:
        raise HTTPException(422, "invalid_period")
    with engine().connect() as db:
        return (
            db.execute(
                text(f"""SELECT r.zone_id,c.collector_id,i.waste_type_id,i.unit,sum(i.quantity) AS quantity,
            count(*) AS collections FROM pickup_requests r JOIN collections c ON c.request_id=r.id
            JOIN collection_items i ON i.collection_id=c.id WHERE {COORD_SCOPE} AND c.confirmed_at IS NOT NULL
            AND c.collected_at>=:start AND c.collected_at<:end
            AND (cast(:zone AS uuid) IS NULL OR r.zone_id=:zone)
            AND (cast(:collector AS uuid) IS NULL OR c.collector_id=:collector)
            GROUP BY r.zone_id,c.collector_id,i.waste_type_id,i.unit
            ORDER BY r.zone_id,c.collector_id,i.waste_type_id,i.unit LIMIT :limit OFFSET :offset"""),
                {
                    "actor": actor.id,
                    "coord_flow": COORDINATORS[actor.role],
                    "zone": zone_id,
                    "collector": collector_id,
                    "start": start,
                    "end": end,
                    "limit": limit,
                    "offset": offset,
                },
            )
            .mappings()
            .all()
        )


@router.get("/public/collection-info", response_model=list[v.Timetable])
def published_schedules(limit: Limit = 50, offset: Offset = 0):
    with engine().connect() as db:
        return (
            db.execute(
                text("""SELECT s.zone_id,z.name AS zone,c.flow,s.generator,s.weekday,s.starts_at,
            s.ends_at,s.timezone,s.valid_from,s.valid_until FROM collection_schedules s JOIN zones z ON z.id=s.zone_id
            JOIN collectives c ON c.id=s.collective_id WHERE z.is_active
            AND (now() AT TIME ZONE 'America/Bogota')::date BETWEEN s.valid_from AND coalesce(s.valid_until,'infinity')
            ORDER BY z.name,s.weekday,s.starts_at,s.id LIMIT :limit OFFSET :offset"""),
                {"limit": limit, "offset": offset},
            )
            .mappings()
            .all()
        )


class CoveragePeriod(Input):
    zone_id: UUID
    valid_from: date
    valid_until: date | None = None

    @model_validator(mode="after")
    def ordered(self):
        if self.valid_until and self.valid_until < self.valid_from:
            raise ValueError("Verifica las fechas de cobertura.")
        return self


@router.put("/admin/members/{member_id}/coverage", response_model=v.Coverage)
def set_coverage(member_id: UUID, body: CoveragePeriod, actor: Admin):
    with engine().begin() as db:
        row = (
            db.execute(
                text("""INSERT INTO collector_zone_coverage(member_id,zone_id,valid_from,valid_until)
            SELECT m.id,z.id,:valid_from,:valid_until FROM collective_members m,zones z WHERE m.id=:member
            AND m.member_role='recolector' AND z.id=:zone_id AND z.is_active
            ON CONFLICT(member_id,zone_id,valid_from) DO UPDATE SET valid_until=excluded.valid_until RETURNING *"""),
                {**body.model_dump(), "member": member_id},
            )
            .mappings()
            .first()
        )
        if not row:
            raise HTTPException(404, "coverage_not_found")
        db.execute(
            text("""INSERT INTO audit_log(actor_id,action,entity,entity_id)
            VALUES (:actor,'coverage.saved','collector_zone_coverage',:id)"""),
            {"actor": actor.id, "id": row["id"]},
        )
        return row


class Zones(Input):
    zone_ids: list[UUID] = Field(max_length=100)


@router.put("/admin/members/{member_id}/zones", response_model=Zones)
def coordinator_zones(member_id: UUID, body: Zones, actor: Admin):
    ids = set(body.zone_ids)
    with engine().begin() as db:
        if not db.scalar(
            text(
                "SELECT id FROM collective_members WHERE id=:member AND member_role='coordinador' FOR UPDATE"
            ),
            {"member": member_id},
        ):
            raise HTTPException(404, "membership_not_found")
        found = (
            db.scalars(
                text("SELECT id FROM zones WHERE is_active AND id=ANY(:ids) FOR SHARE"),
                {"ids": list(ids)},
            ).all()
            if ids
            else []
        )
        if set(found) != ids:
            raise HTTPException(422, "inactive_zone")
        db.execute(
            text("DELETE FROM coordinator_zones WHERE member_id=:id"), {"id": member_id}
        )
        if ids:
            db.execute(
                text(
                    "INSERT INTO coordinator_zones(member_id,zone_id) VALUES (:member,:zone)"
                ),
                [{"member": member_id, "zone": z} for z in ids],
            )
        db.execute(
            text("""INSERT INTO audit_log(actor_id,action,entity,entity_id)
            VALUES (:actor,'coordinator.zones_updated','collective_members',:id)"""),
            {"actor": actor.id, "id": member_id},
        )
    return body


@router.get("/admin/members", response_model=list[v.MemberView])
def members(actor: Admin, limit: Limit = 50, offset: Offset = 0):
    with engine().connect() as db:
        return (
            db.execute(
                text("""SELECT m.id,m.user_id,m.collective_id,m.member_role,
            ARRAY(SELECT zone_id FROM coordinator_zones WHERE member_id=m.id ORDER BY zone_id) AS coordinator_zones
            FROM collective_members m ORDER BY m.id LIMIT :limit OFFSET :offset"""),
                {"limit": limit, "offset": offset},
            )
            .mappings()
            .all()
        )

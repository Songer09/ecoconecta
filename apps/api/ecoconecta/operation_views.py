from datetime import date, datetime, time
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class ID(BaseModel):
    id: UUID


class ProfileView(BaseModel):
    full_name: str
    address: str | None
    generator_type: str | None
    neighborhood: str | None
    business_name: str | None


class Membership(BaseModel):
    user_id: UUID
    member_id: UUID


class AvailableGroup(BaseModel):
    collective_id: UUID
    is_available: bool


class Coverage(ID):
    member_id: UUID
    zone_id: UUID
    valid_from: date
    valid_until: date | None


class MaterialTotal(BaseModel):
    zone_id: UUID
    collector_id: UUID
    waste_type_id: UUID
    unit: str
    quantity: Decimal
    collections: int


class Timetable(BaseModel):
    zone_id: UUID
    zone: str
    flow: str
    generator: str
    weekday: int
    starts_at: time
    ends_at: time
    timezone: str
    valid_from: date
    valid_until: date | None


class RewardView(ID):
    name: str
    price: int
    stock: int


class Redemption(ID):
    user_id: UUID
    reward_id: UUID
    quantity: int
    cost: Decimal
    created_at: datetime


class Stop(ID):
    code: str
    address: str
    latitude: Decimal | None
    longitude: Decimal | None
    scheduled_start: datetime
    scheduled_end: datetime | None
    stop_order: int | None
    collector_id: UUID


class GardenNeed(ID):
    zone_id: UUID
    name: str
    unit: str
    quantity: Decimal
    updated_at: datetime


class LastPosition(BaseModel):
    collector_id: UUID
    zone_id: UUID
    request_id: UUID
    latitude: float
    longitude: float
    accuracy_m: float
    updated_at: datetime


class PurchaseRate(ID):
    material_id: UUID
    valid_from: datetime
    cop_per_kg: Decimal
    source: str


class PurchaseValue(BaseModel):
    collective_id: UUID
    waste_type_id: UUID
    kg: Decimal
    estimated_cop: Decimal | None
    missing_prices: int


class Movement(ID):
    collection_id: UUID | None
    reason: str
    points: Decimal
    created_at: datetime


class MemberView(ID):
    user_id: UUID
    collective_id: UUID
    member_role: str
    coordinator_zones: list[UUID]


class RequestCount(BaseModel):
    flow: str
    status: str
    requests: int


class ConfiguredZone(ID):
    code: str
    name: str
    is_active: bool


class ConfiguredMaterial(ID):
    name: str
    flow: str
    unit: str
    is_active: bool


class ConfiguredGroup(ID):
    name: str
    flow: str

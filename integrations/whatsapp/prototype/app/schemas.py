from decimal import Decimal
from typing import Annotated, Literal
from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    model_validator,
)


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


Short = Annotated[str, StringConstraints(min_length=1, max_length=160)]
Flow = Literal["organic", "recyclable"]
Unit = Literal[
    "kg",
    "bolsas",
    "costales",
    "canecas",
    "baldes",
    "unidades",
    "l",
    "cajas",
    "botellas",
    "bultos",
]
Quantity = Annotated[Decimal, Field(gt=0, le=100000, max_digits=12, decimal_places=3)]


class Message(Strict):
    text: str = Field(min_length=1, max_length=2000)
    kind: Literal["text", "demo_audio"] = "text"
    message_id: Short | None = None


class Assignment(Strict):
    collector_id: int = Field(gt=0)


class Schedule(Strict):
    scheduled_at: AwareDatetime


class CollectedItem(Strict):
    material: Short
    quantity: Quantity
    unit: Unit


class Collection(Strict):
    quantity: Quantity | None = None
    unit: Unit | None = None
    items: list[CollectedItem] | None = Field(default=None, min_length=1, max_length=20)

    @model_validator(mode="after")
    def required_shape(self):
        if self.items is None:
            if self.quantity is None or self.unit is None:
                raise ValueError("Indica cantidad y unidad")
        elif (
            self.quantity is not None
            or self.unit is not None
            or len({i.material for i in self.items}) != len(self.items)
        ):
            raise ValueError("Indica una verificación por material")
        return self


class Event(Strict):
    kind: Literal["event", "training"]
    title: Short
    category: Short
    place: Short
    organizer: Short
    starts_at: AwareDatetime
    description: str = Field(min_length=1, max_length=1000)
    published: bool = False


class Article(Strict):
    title: Short
    keywords: Short
    source: str = Field(min_length=4, max_length=300)
    answer: str = Field(min_length=4, max_length=1000)
    published: bool = False


class Rule(Strict):
    material: Short
    unit: Unit
    rate: Quantity
    starts_at: AwareDatetime
    ends_at: AwareDatetime | None = None

    @model_validator(mode="after")
    def valid_dates(self):
        if self.ends_at and self.ends_at <= self.starts_at:
            raise ValueError("Vigencia inválida")
        return self


class Material(Strict):
    name: Short
    flow: Flow
    accepted: bool = False

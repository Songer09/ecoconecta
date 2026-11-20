from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class EnvironmentalDecision(str, Enum):
    COMPOSTABLE = "COMPOSTABLE"
    NO_COMPOSTABLE = "NO_COMPOSTABLE"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"


class WasteCategory(str, Enum):
    ORGANIC = "organic"
    INORGANIC = "inorganic"


class EnvironmentalResult(BaseModel):
    decision: EnvironmentalDecision
    profile: str
    reason: str


class RecognitionResponse(BaseModel):
    request_id: str
    status: str = Field(description="recognized, review_required, or unknown")
    material: str | None
    predicted_class: str | None
    waste_category: WasteCategory | None = Field(description="Categoría general solo si está definida por reglas explícitas.")
    confidence: float | None = Field(ge=0, le=1)
    confidence_calibrated: bool = Field(description="False hasta entrenar y validar un calibrador separado.")
    confidence_margin: float | None = Field(ge=0, le=1)
    out_of_distribution: bool
    environmental: EnvironmentalResult
    justification: str
    handling_recommendation: str
    manual_review_required: bool
    model_version: str
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

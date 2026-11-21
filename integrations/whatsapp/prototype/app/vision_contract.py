"""Contrato para conectar un clasificador visual cuando exista un adaptador autorizado."""

from typing import Protocol
from pydantic import BaseModel, Field


class VisualSuggestion(BaseModel):
    material: str
    confidence: float = Field(ge=0, le=1)
    model_version: str
    needs_review: bool


class VisionProvider(Protocol):
    def suggest(self, image: bytes, mime: str) -> list[VisualSuggestion]: ...

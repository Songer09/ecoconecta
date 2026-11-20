from __future__ import annotations

import io
import os
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from PIL import Image, UnidentifiedImageError

from compost_ai.contracts import EnvironmentalDecision, EnvironmentalResult, RecognitionResponse
from compost_ai.model import WasteRecognizer
from compost_ai.rules import EnvironmentalRules

MODEL_DIR = Path(os.getenv("COMPOST_MODEL_DIR", "artifacts/model_bdwaste_individual"))
RULES_PATH = Path(os.getenv("COMPOST_RULES_PATH", "config/environmental_rules.yaml"))
MAX_IMAGE_BYTES = int(os.getenv("COMPOST_MAX_IMAGE_BYTES", "10485760"))
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.recognizer = WasteRecognizer(MODEL_DIR)
    app.state.rules = EnvironmentalRules(RULES_PATH)
    yield


app = FastAPI(
    title="COMPOST AI Recognition API",
    version="1.0.0",
    description="Technology-independent waste recognition and facility-rule decisions.",
    lifespan=lifespan,
)


@app.post("/api/v1/recognize", response_model=RecognitionResponse, tags=["recognition"])
async def recognize(
    request: Request,
    image: UploadFile = File(..., description="JPEG, PNG, or WEBP image; up to 10 MiB."),
    compost_profile: str = Form("household", description="household, community, or industrial"),
):
    request_id = str(uuid.uuid4())
    rules: EnvironmentalRules = request.app.state.rules
    try:
        rules.decide(compost_profile, None, False)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    data = await image.read(MAX_IMAGE_BYTES + 1)
    if len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail=f"Image exceeds {MAX_IMAGE_BYTES} bytes.")
    try:
        decoded = Image.open(io.BytesIO(data))
        decoded.verify()
        decoded = Image.open(io.BytesIO(data))
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise HTTPException(status_code=415, detail="Upload is not a valid supported image.") from exc
    if decoded.format not in ALLOWED_FORMATS:
        raise HTTPException(status_code=415, detail="Supported image formats are JPEG, PNG, and WEBP.")
    decoded = decoded.convert("RGB")
    result = request.app.state.recognizer.predict(decoded)
    environmental = rules.decide(compost_profile, result["predicted_class"], result["accepted"])
    status = "recognized" if result["accepted"] else ("unknown" if result["out_of_distribution"] else "review_required")
    decision = getattr(environmental.decision, "value", environmental.decision)
    manual_review = (not result["accepted"]) or decision == "REQUIRES_REVIEW"
    if manual_review:
        recommendation = "Retener para revisión manual; no aprobar compostaje todavía."
    elif decision == "NO_COMPOSTABLE":
        recommendation = "Excluir del flujo de compostaje según las reglas del perfil."
    else:
        recommendation = "Seguir las condiciones definidas por las reglas del perfil."
    category = rules.category_for(result["predicted_class"]) if result["accepted"] else None
    return RecognitionResponse(
        request_id=request_id,
        status=status,
        material=result["material"] if result["accepted"] else None,
        predicted_class=result["predicted_class"],
        waste_category=category,
        confidence=result["confidence"],
        confidence_calibrated=bool(request.app.state.recognizer.metadata.get("confidence_calibrated", False)),
        confidence_margin=result["confidence_margin"],
        out_of_distribution=result["out_of_distribution"],
        environmental=environmental,
        justification=environmental.reason,
        handling_recommendation=recommendation,
        manual_review_required=manual_review,
        model_version=request.app.state.recognizer.metadata.get("model_version", "unversioned"),
        warnings=[] if result["accepted"] else ["Prediction requires manual review."],
        metadata={"candidate_class": result["candidate_class"], "ood_distance": result["ood_distance"]},
    )

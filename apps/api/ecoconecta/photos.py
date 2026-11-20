import os
from io import BytesIO
from typing import Literal

import httpx
from pydantic import BaseModel, Field, ValidationError

from fastapi import APIRouter, HTTPException, Request, Response
from PIL import Image, ImageOps, UnidentifiedImageError
from starlette.concurrency import run_in_threadpool

from .auth import Actor
from .operations import resident

router = APIRouter(tags=["Fotos"])
MAX_BYTES = 5 * 1024 * 1024


def normalize(data, content_type):
    try:
        with Image.open(BytesIO(data), formats=["JPEG", "PNG"]) as img:
            if Image.MIME[img.format] != content_type:
                raise HTTPException(422, "invalid_image_type")
            if img.width * img.height > 12000000 or getattr(img, "is_animated", False):
                raise HTTPException(422, "invalid_image")
            img.load()
            rgb = ImageOps.exif_transpose(img).convert("RGB")
            rgb.thumbnail((1600, 1600))
            output = BytesIO()
            rgb.info.clear()
            rgb.save(output, format="JPEG", quality=85, exif=b"")
            return output.getvalue()
    except (
        UnidentifiedImageError,
        OSError,
        ValueError,
        Image.DecompressionBombError,
    ) as error:
        raise HTTPException(422, "invalid_image") from error


async def normalized_upload(request: Request):
    if request.headers.get("content-type") not in ("image/jpeg", "image/png"):
        raise HTTPException(415, "unsupported_image_type")
    data = bytearray()
    async for chunk in request.stream():
        if len(data) + len(chunk) > MAX_BYTES:
            raise HTTPException(413, "image_too_large")
        data.extend(chunk)
    return await run_in_threadpool(normalize, data, request.headers["content-type"])


@router.post(
    "/users/me/photo-preview",
    response_class=Response,
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                mime: {"schema": {"type": "string", "format": "binary"}}
                for mime in ("image/jpeg", "image/png")
            },
        }
    },
    responses={200: {"content": {"image/jpeg": {}}}},
)
async def preview(request: Request, actor: Actor):
    resident(actor)
    return Response(await normalized_upload(request), media_type="image/jpeg")


class Suggestion(BaseModel):
    status: Literal["recognized", "review_required", "unknown"]
    material: str | None
    waste_category: Literal["organic", "inorganic"] | None
    confidence: float | None = Field(ge=0, le=1)
    confidence_calibrated: bool
    manual_review_required: bool
    model_version: str = Field(min_length=1)


@router.post("/users/me/photo-recognition", response_model=Suggestion,
             openapi_extra={"requestBody":{"required":True,"content":{
                 mime:{"schema":{"type":"string","format":"binary"}} for mime in ("image/jpeg","image/png")}}})
async def recognize(request: Request, actor: Actor):
    resident(actor)
    base_url = os.getenv("COMPOST_AI_BASE_URL")
    if not base_url:
        raise HTTPException(503, "vision_unavailable")
    photo = await normalized_upload(request)
    try:
        async with httpx.AsyncClient(timeout=10, trust_env=False) as client:
            result = await client.post(base_url.rstrip("/") + "/api/v1/recognize",
                                       files={"image": ("photo.jpg", photo, "image/jpeg")},
                                       data={"compost_profile": "household"})
            result.raise_for_status()
            suggestion = Suggestion.model_validate_json(result.content)
    except (httpx.HTTPError, ValidationError):
        raise HTTPException(503, "vision_unavailable") from None
    if suggestion.status != "recognized" or suggestion.manual_review_required:
        suggestion.material = None
        suggestion.waste_category = None
        suggestion.manual_review_required = True
    return suggestion

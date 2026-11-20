from io import BytesIO

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
    if request.headers.get("content-type") not in ("image/jpeg", "image/png"):
        raise HTTPException(415, "unsupported_image_type")
    data = bytearray()
    async for chunk in request.stream():
        if len(data) + len(chunk) > MAX_BYTES:
            raise HTTPException(413, "image_too_large")
        data.extend(chunk)
    return Response(
        await run_in_threadpool(normalize, data, request.headers["content-type"]),
        media_type="image/jpeg",
    )

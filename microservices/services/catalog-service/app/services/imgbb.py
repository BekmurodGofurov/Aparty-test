"""ImgBB Image Upload Service module inside Catalog Service."""

from __future__ import annotations

import base64
import logging
import httpx
from fastapi import HTTPException, UploadFile, status

from app.config import settings
from app.schemas import ImageUploadResponse

logger = logging.getLogger(__name__)

IMGBB_UPLOAD_URL: str = "https://api.imgbb.com/1/upload"
ALLOWED_EXTENSIONS: frozenset[str] = frozenset({"jpg", "jpeg", "png", "webp"})
ALLOWED_CONTENT_TYPES: frozenset[str] = frozenset({"image/jpeg", "image/png", "image/webp"})
MAX_FILE_SIZE_BYTES: int = 5 * 1024 * 1024  # 5 MB


async def upload_image_to_imgbb(file: UploadFile) -> ImageUploadResponse:
    """Upload image to ImgBB and return display_url and delete_url."""
    filename = file.filename or ""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Faqat .jpg, .jpeg, .png yoki .webp formatdagi fayllar qabul qilinadi.",
        )

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Noto'g'ri fayl turi. Faqat rasm fayllarini yuklash mumkin.",
        )

    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Fayl hajmi 5 MB dan oshmasligi kerak.",
        )

    if not settings.imgbb_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ImgBB API kaliti sozlanmagan. Rasm yuklash xizmati mavjud emas.",
        )

    image_b64 = base64.b64encode(file_bytes).decode("utf-8")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            IMGBB_UPLOAD_URL,
            params={"key": settings.imgbb_api_key},
            data={"image": image_b64, "name": filename},
        )

    if response.status_code != 200:
        logger.error("ImgBB upload failed (%d): %s", response.status_code, response.text)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="ImgBB xizmatiga rasmni yuklashda xatolik yuz berdi.",
        )

    payload = response.json()
    if not payload.get("success"):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="ImgBB xizmati muvaffaqiyatsiz javob qaytardi.",
        )

    data = payload.get("data", {})
    display_url = data.get("display_url") or data.get("url") or ""
    delete_url = data.get("delete_url")

    return ImageUploadResponse(
        display_url=display_url,
        delete_url=delete_url,
        provider="imgbb",
    )

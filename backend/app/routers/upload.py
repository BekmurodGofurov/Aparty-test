"""
Cloud image upload router.

All images are forwarded to the ImgBB API and the permanent CDN URL is
returned to the caller.  No files are ever written to the local filesystem.
"""

import base64

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.config import settings
from app.dependencies.auth import get_current_user
from app.models.user import User

router = APIRouter()

# ── Validation constants ─────────────────────────────────────────────────────

# Strict allowlist — SVG, executables, and every other type are rejected.
ALLOWED_EXTENSIONS: frozenset[str] = frozenset({"jpg", "jpeg", "png", "webp"})
ALLOWED_CONTENT_TYPES: frozenset[str] = frozenset(
    {"image/jpeg", "image/png", "image/webp"}
)

MAX_FILE_SIZE_BYTES: int = 5 * 1024 * 1024  # 5 MB

IMGBB_UPLOAD_URL: str = "https://api.imgbb.com/1/upload"


# ── Endpoint ─────────────────────────────────────────────────────────────────


@router.post("/image", status_code=status.HTTP_201_CREATED)
async def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    """Upload an image to ImgBB and return its permanent CDN URL."""

    # ── 1. Extension validation ──────────────────────────────────────────────
    filename = file.filename or ""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Faqat .jpg, .jpeg, .png yoki .webp formatdagi fayllar qabul qilinadi. "
                ".svg va bajariladigan fayllar taqiqlangan."
            ),
        )

    # ── 2. Content-type validation ───────────────────────────────────────────
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Noto'g'ri fayl turi. Faqat rasm fayllarini yuklash mumkin.",
        )

    # ── 3. Read file & size validation ───────────────────────────────────────
    raw_bytes = await file.read()

    if len(raw_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Fayl hajmi 5 MB dan oshmasligi kerak.",
        )

    # ── 4. ImgBB API key check ───────────────────────────────────────────────
    if not settings.imgbb_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Rasm yuklash xizmati hozircha mavjud emas (API kalit yo'q).",
        )

    # ── 5. Upload to ImgBB ───────────────────────────────────────────────────
    image_b64 = base64.b64encode(raw_bytes).decode("utf-8")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            IMGBB_UPLOAD_URL,
            params={"key": settings.imgbb_api_key},
            data={"image": image_b64},
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Rasm yuklashda xatolik yuz berdi. Iltimos qayta urinib ko'ring.",
        )

    payload = response.json()
    if not payload.get("success"):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="ImgBB xizmati muvaffaqiyatsiz javob qaytardi.",
        )

    # ImgBB returns data.url for the direct display link
    image_url: str = payload["data"]["url"]
    return {"url": image_url}

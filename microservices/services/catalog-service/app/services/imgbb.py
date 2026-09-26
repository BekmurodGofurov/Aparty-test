"""ImgBB image upload."""

from __future__ import annotations

import base64
import logging

import httpx
from fastapi import HTTPException, UploadFile, status

from app.config import settings
from app.constants import ALLOWED_IMAGE_CONTENT_TYPES, ALLOWED_IMAGE_EXTENSIONS
from app.schemas import ImageUploadResponse

logger = logging.getLogger(__name__)

UPLOAD_TIMEOUT_SECONDS = 30.0
PAYLOAD_TOO_LARGE_STATUS = 413


def _bad_request(detail: str, code: int = status.HTTP_400_BAD_REQUEST) -> HTTPException:
    return HTTPException(status_code=code, detail=detail)


async def upload_image_to_imgbb(file: UploadFile) -> ImageUploadResponse:
    """Validate an image, upload it to ImgBB and return its display and delete URLs."""
    filename = file.filename or ""
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        raise _bad_request("Only .jpg, .jpeg, .png and .webp files are accepted.")
    if file.content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
        raise _bad_request("Invalid file type. Only image files can be uploaded.")

    file_bytes = await file.read()
    if len(file_bytes) > settings.max_upload_size_bytes:
        max_mb = settings.max_upload_size_bytes // (1024 * 1024)
        raise _bad_request(f"File size must not exceed {max_mb} MB.", PAYLOAD_TOO_LARGE_STATUS)

    if not settings.imgbb_api_key:
        raise _bad_request("Image upload is not configured.", status.HTTP_503_SERVICE_UNAVAILABLE)

    async with httpx.AsyncClient(timeout=UPLOAD_TIMEOUT_SECONDS) as client:
        response = await client.post(
            settings.imgbb_upload_url,
            params={"key": settings.imgbb_api_key},
            data={"image": base64.b64encode(file_bytes).decode("utf-8"), "name": filename},
        )

    if response.status_code != 200:
        logger.error("ImgBB upload failed (%d): %s", response.status_code, response.text)
        raise _bad_request("Image upload to ImgBB failed.", status.HTTP_502_BAD_GATEWAY)

    payload = response.json()
    if not payload.get("success"):
        raise _bad_request("ImgBB returned an unsuccessful response.", status.HTTP_502_BAD_GATEWAY)

    data = payload.get("data", {})
    display_url = data.get("display_url") or data.get("url") or ""
    return ImageUploadResponse(url=display_url, display_url=display_url, delete_url=data.get("delete_url"))

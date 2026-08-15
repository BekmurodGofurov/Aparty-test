"""Catalog Service Media Router (`/api/v1/media`)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, UploadFile, status

from app.schemas import ImageUploadResponse
from app.security import get_current_owner_id
from app.services.imgbb import upload_image_to_imgbb

router = APIRouter(prefix="/api/v1/media", tags=["Media"])


@router.post("/upload", status_code=status.HTTP_201_CREATED, response_model=ImageUploadResponse)
@router.post("/image", status_code=status.HTTP_201_CREATED, response_model=ImageUploadResponse)
async def upload_image(
    file: UploadFile = File(...),
    current_user_id: int = Depends(get_current_owner_id),
) -> ImageUploadResponse:
    """Upload an image to ImgBB and return CDN display_url and delete_url."""
    return await upload_image_to_imgbb(file)

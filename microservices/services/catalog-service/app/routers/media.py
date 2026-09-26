"""Catalog Service Media Router (`/api/v1/media`). Images only."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, UploadFile, status

from app.constants import ALL_ROLES, API_PREFIX
from app.schemas import ImageUploadResponse
from app.security import CurrentUser, require_roles
from app.services.imgbb import upload_image_to_imgbb

router = APIRouter(prefix=f"{API_PREFIX}/media", tags=["Media"])


@router.post("/upload", status_code=status.HTTP_201_CREATED, response_model=ImageUploadResponse)
@router.post("/image", status_code=status.HTTP_201_CREATED, response_model=ImageUploadResponse)
async def upload_image(
    file: UploadFile = File(...),
    _user: CurrentUser = Depends(require_roles(*ALL_ROLES)),
) -> ImageUploadResponse:
    """Upload an image and return its CDN URLs."""
    return await upload_image_to_imgbb(file)

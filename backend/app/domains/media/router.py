from fastapi import APIRouter, Depends, File, UploadFile, status
from app.domains.users.services import get_current_user
from app.domains.users.models import User
from app.domains.media.schemas import ImageUploadResponse
from app.domains.media.services import MediaService

router = APIRouter()

@router.post("/image", status_code=status.HTTP_201_CREATED, response_model=ImageUploadResponse)
async def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
) -> ImageUploadResponse:
    """Upload an image to ImgBB and return its permanent CDN URL."""
    url = await MediaService.upload_image(file)
    return ImageUploadResponse(url=url)

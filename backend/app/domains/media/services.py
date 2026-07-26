import base64
import httpx
from fastapi import HTTPException, UploadFile, status
from app.core.config import settings

ALLOWED_EXTENSIONS: frozenset[str] = frozenset({"jpg", "jpeg", "png", "webp"})
ALLOWED_CONTENT_TYPES: frozenset[str] = frozenset({"image/jpeg", "image/png", "image/webp"})
MAX_FILE_SIZE_BYTES: int = 5 * 1024 * 1024  # 5 MB
IMGBB_UPLOAD_URL: str = "https://api.imgbb.com/1/upload"

class MediaService:
    @staticmethod
    async def upload_image(file: UploadFile) -> str:
        filename = file.filename or ""
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Faqat .jpg, .jpeg, .png yoki .webp formatdagi fayllar qabul qilinadi. .svg va bajariladigan fayllar taqiqlangan.",
            )

        if file.content_type not in ALLOWED_CONTENT_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Noto'g'ri fayl turi. Faqat rasm fayllarini yuklash mumkin.",
            )

        raw_bytes = await file.read()

        if len(raw_bytes) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Fayl hajmi 5 MB dan oshmasligi kerak.",
            )

        if not settings.imgbb_api_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Rasm yuklash xizmati hozircha mavjud emas (API kalit yo'q).",
            )

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

        return payload["data"]["url"]

import io
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError

from app.core.config import get_settings

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/bmp"}
IMAGE_SUFFIXES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp", "image/bmp": ".bmp"}


def upload_root() -> Path:
    root = Path(get_settings().upload_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


async def read_valid_image(file: UploadFile) -> tuple[bytes, str]:
    content_type = (file.content_type or "").lower()
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=415, detail="Only JPEG, PNG, WEBP, and BMP images are accepted.")
    image_bytes = await file.read(get_settings().max_image_size + 1)
    if len(image_bytes) > get_settings().max_image_size:
        raise HTTPException(status_code=413, detail="Image exceeds the configured size limit.")
    try:
        with Image.open(io.BytesIO(image_bytes)) as image:
            image.verify()
    except (UnidentifiedImageError, OSError):
        raise HTTPException(status_code=415, detail="The uploaded file is not a valid image.")
    return image_bytes, content_type


def save_image(image_bytes: bytes, content_type: str) -> str:
    stored_filename = f"{uuid4().hex}{IMAGE_SUFFIXES[content_type]}"
    (upload_root() / stored_filename).write_bytes(image_bytes)
    return stored_filename


def image_path(stored_filename: str) -> Path:
    root = upload_root()
    candidate = (root / stored_filename).resolve()
    if candidate.parent != root:
        raise HTTPException(status_code=404, detail="Image not found.")
    return candidate

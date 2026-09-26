import os
import uuid
from typing import Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.dependency import get_current_user
from app.db.session import get_async_db
from app.models.uploads import Upload
from app.models.user import User

router = APIRouter(prefix="/uploads", tags=["uploads"])

MAX_FILE_SIZE = 5 * 1024 * 1024
UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

IMAGE_SIGNATURES: dict[str, tuple[str, bytes]] = {
    "image/jpeg": (".jpg", b"\xff\xd8\xff"),
    "image/jpg": (".jpg", b"\xff\xd8\xff"),
    "image/png": (".png", b"\x89PNG\r\n\x1a\n"),
    "image/gif": (".gif", b"GIF8"),
}


def get_image_extension(content_type: str | None, content: bytes) -> str | None:
    if not content_type:
        return None

    mime_type = content_type.lower().split(";", maxsplit=1)[0].strip()
    if mime_type == "image/webp":
        return ".webp" if content.startswith(b"RIFF") and content[8:12] == b"WEBP" else None

    signature = IMAGE_SIGNATURES.get(mime_type)
    if signature and content.startswith(signature[1]):
        return signature[0]
    return None


@router.post("/image", status_code=status.HTTP_201_CREATED)
async def upload_image(
    file: UploadFile = File(...),
    purpose: Literal["avatar", "service"] = Form("avatar"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    content = await file.read(MAX_FILE_SIZE + 1)
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Image must be 5MB or smaller.",
        )

    extension = get_image_extension(file.content_type, content)
    if extension is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image file. Allowed formats: JPEG, PNG, WEBP, GIF.",
        )

    filename = f"{uuid.uuid4().hex}{extension}"
    target_path = os.path.join(UPLOAD_DIR, filename)

    try:
        with open(target_path, "wb") as image_file:
            image_file.write(content)

        upload = Upload(
            filename=filename,
            url=f"/uploads/{filename}",
            purpose=purpose,
            owner_id=current_user.id,
        )
        db.add(upload)
        await db.commit()
        await db.refresh(upload)
    except Exception:
        if os.path.exists(target_path):
            os.remove(target_path)
        await db.rollback()
        raise
    finally:
        await file.close()

    return {"id": upload.id, "url": upload.url, "filename": upload.filename}


@router.delete("/{upload_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_unattached_upload(
    upload_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Upload).where(
            Upload.id == upload_id,
            Upload.owner_id == current_user.id,
            Upload.service_id.is_(None),
        )
    )
    upload = result.scalar_one_or_none()
    if not upload:
        raise HTTPException(status_code=404, detail="Unattached image not found")

    target_path = os.path.join(UPLOAD_DIR, upload.filename)
    await db.delete(upload)
    await db.commit()
    try:
        os.remove(target_path)
    except FileNotFoundError:
        pass
    return None

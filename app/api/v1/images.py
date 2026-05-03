
from fastapi import APIRouter, Depends, UploadFile, File, Response, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.image import Image

router = APIRouter(prefix="/images", tags=["Images"])

@router.post("/")
async def upload_image(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):

    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image.")

    data = await file.read()

    image = Image(
        filename=file.filename,
        content_type=file.content_type,
        data=data
    )
    db.add(image)
    await db.commit()
    await db.refresh(image)

    return {"url": f"/api/v1/images/{image.id}"}

@router.get("/{image_id}")
async def get_image(
    image_id: str,
    db: AsyncSession = Depends(get_db)
):

    result = await db.execute(select(Image).where(Image.id == image_id))
    image = result.scalar_one_or_none()

    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    return Response(content=image.data, media_type=image.content_type)
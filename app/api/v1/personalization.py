
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.personalization import PersonalizationResponse, PersonalizationUpdate
from app.services.personalization_service import PersonalizationService
from app.services.upload_service import UploadService

router = APIRouter(prefix="/baskets/{basket_id}/personalization", tags=["Personalization"])

@router.get(
    "/",
    response_model=PersonalizationResponse,
    summary="Get basket personalization (FR18–FR21)",
)
async def get_personalization(
    basket_id: str,
    db: AsyncSession = Depends(get_db),
):

    service = PersonalizationService(db)
    return await service.get_personalization(basket_id)

@router.put(
    "/",
    response_model=PersonalizationResponse,
    summary="Set or update personalization (FR18, FR19, FR21)",
)
async def upsert_personalization(
    basket_id: str,
    data: PersonalizationUpdate,
    db: AsyncSession = Depends(get_db),
):

    service = PersonalizationService(db)
    return await service.upsert_personalization(basket_id, data)

@router.post(
    "/upload",
    response_model=PersonalizationResponse,
    summary="Upload gift-tag image (FR20)",
)
async def upload_gift_tag(
    basket_id: str,
    file: UploadFile = File(..., description="Image file for the printed gift tag."),
    db: AsyncSession = Depends(get_db),
):

    try:
        upload_service = UploadService()
        image_url = await upload_service.upload_gift_tag(file)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    pers_service = PersonalizationService(db)
    return await pers_service.set_gift_tag_image(basket_id, image_url)
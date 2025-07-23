from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from cor_lab.database.db import get_db
from cor_lab.schemas import (
    ChangeGlassStaining,
    DeleteGlassesRequest,
    DeleteGlassesResponse,
    Glass as GlassModelScheema,
    GlassCreate,
    GlassPrinting,
)
from cor_lab.repository import glass as glass_service
from typing import List

from cor_lab.services.access import doctor_access
from loguru import logger


router = APIRouter(prefix="/glasses", tags=["Glass"])


@router.post(
    "/create",
    dependencies=[Depends(doctor_access)],
    response_model=List[GlassModelScheema],
)
async def create_glass_for_cassette(
    body: GlassCreate,
    printing: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """Создаем указанное количество стёкол"""
    return await glass_service.create_glass(
        db=db,
        cassette_id=body.cassette_id,
        num_glasses=body.num_glasses,
        staining_type=body.staining_type,
        printing=printing,
    )


@router.get(
    "/{glass_id}",
    response_model=GlassModelScheema,
    dependencies=[Depends(doctor_access)],
)
async def read_glass_info(glass_id: str, db: AsyncSession = Depends(get_db)):
    """Получаем информацию о стекле по его ID."""
    db_glass = await glass_service.get_glass(db=db, glass_id=glass_id)
    if db_glass is None:
        raise HTTPException(status_code=404, detail="Glass not found")
    return db_glass


@router.delete(
    "/delete",
    response_model=DeleteGlassesResponse,
    dependencies=[Depends(doctor_access)],
    status_code=status.HTTP_200_OK,
)
async def delete_glasses_endpoint(
    request_body: DeleteGlassesRequest, db: AsyncSession = Depends(get_db)
):
    """Удаляет несколько стекол по их ID."""
    result = await glass_service.delete_glasses(db=db, glass_ids=request_body.glass_ids)
    return result


@router.patch(
    "/{glass_id}/staining",
    response_model=GlassModelScheema,
    dependencies=[Depends(doctor_access)],
)
async def change_glass_staining(
    glass_id: str, body: ChangeGlassStaining, db: AsyncSession = Depends(get_db)
):
    """Получаем информацию о стекле по его ID."""
    db_glass = await glass_service.change_staining(db=db, glass_id=glass_id, body=body)
    if db_glass is None:
        raise HTTPException(status_code=404, detail="Glass not found")
    return db_glass


@router.patch(
    "/{glass_id}/printed",
    response_model=GlassModelScheema,
    dependencies=[Depends(doctor_access)],
)
async def change_glass_printing_status(
    data: GlassPrinting, request: Request, db: AsyncSession = Depends(get_db)
):
    """Меняем статус печати стекла"""

    print_result = await glass_service.print_glass_data(db=db, data=data, request=request)

    if print_result and print_result.get("success"):
        updated_glass = await glass_service.change_printing_status(
            db=db, glass_id=data.glass_id, printing=data.printing 
        )
        if updated_glass is None:
            logger.warning(f"Предупреждение: Стекло {data.glass_id} не найдено для обновления статуса после успешной печати.")
        
        return updated_glass

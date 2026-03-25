from sqlalchemy.orm import selectinload
from app.models.category import Category
from app.schemas.category import CategoryRead,CategoryReadWithServices,CategoryCreate
from app.api.v1.endpoints.dependency import get_current_active_superuser
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import APIRouter, Depends, HTTPException, status
from app.db.session import get_async_db

router = APIRouter(prefix="/categories", tags=["categories"])

@router.post("/create",response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
async def create_category(category_in:CategoryCreate, db:AsyncSession = Depends(get_async_db), current_user = Depends(get_current_active_superuser)):
    result=await db.execute(select(Category).where(Category.name == category_in.name))
    if result.scalars().first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category with this name already exists")
    new_category=Category(**category_in.model_dump())
    db.add(new_category)
    await db.commit()
    await db.refresh(new_category)
    return new_category

@router.get("/{category_id}", response_model=CategoryReadWithServices)
async def get_category(category_id:int,db:AsyncSession = Depends(get_async_db)):
    result=await db.execute(select(Category).options(selectinload(Category.services)).where(Category.id == category_id))
    category=result.scalars().first()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return category
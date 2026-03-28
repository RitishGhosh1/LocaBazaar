from sqlalchemy.orm import selectinload
from app.models.category import Category
from app.schemas.category import CategoryRead,CategoryReadWithServices,CategoryCreate
from app.api.v1.endpoints.dependency import get_current_active_superuser
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import APIRouter, Depends, HTTPException, status
from app.db.session import get_async_db

from app.core.redis import redis_cache

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
    await redis_cache.delete("categories:all")
    return new_category

@router.get("/{category_id}", response_model=CategoryReadWithServices)
async def get_category(category_id:int,db:AsyncSession = Depends(get_async_db)):
    result=await db.execute(select(Category).options(selectinload(Category.services)).where(Category.id == category_id))
    category=result.scalars().first()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return category


@router.get("/", response_model=list[CategoryRead])
async def get_all_categories(db: AsyncSession = Depends(get_async_db)):
    cache_key = "categories:all"

    # 1. TRY: Check Redis
    cached_data = await redis_cache.get(cache_key)
    if cached_data:
        # If it exists, FastAPI will automatically convert 
        # the list of dicts into CategoryRead objects
        return cached_data

    # 2. MISS: Go to Postgres
    result = await db.execute(select(Category))
    categories = result.scalars().all()

    # 3. CONVERT: Turn SQLAlchemy objects into plain dicts
    # Redis can't store Class objects, only text (JSON)
    categories_data = [
        {"id": c.id, "name": c.name, "description": c.description} 
        for c in categories
    ]

    # 4. SAVE: Store in Redis for 1 hour (3600 seconds)
    await redis_cache.set(cache_key, categories_data, expire=3600)

    return categories_data
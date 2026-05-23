from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.session import get_async_db
from app.models.user import User, UserRole
from app.models.services import Service
from app.models.booking import Booking
from app.api.v1.endpoints.dependency import get_current_user
from sqlalchemy import update, delete
# --- Governance Dependency ---
async def get_superuser(user: User = Depends(get_current_user)):
    if not user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Superuser access required"
        )
    return user

router = APIRouter(prefix="/admin", tags=["admin"])

# 1. Platform-wide Stats (The "Landlord" View)
@router.get("/dashboard/stats", include_in_schema=True)
async def get_platform_stats(
    db: AsyncSession = Depends(get_async_db),
    admin: User = Depends(get_superuser),
):
    total_users = await db.execute(select(func.count()).select_from(User))
    total_services = await db.execute(select(func.count()).select_from(Service))
    pending_bookings = await db.execute(
        select(func.count()).select_from(Booking).where(Booking.status == "pending")
    )
    return {
        "total_users": total_users.scalar(),
        "total_services": total_services.scalar(),
        "pending_bookings": pending_bookings.scalar(),
    }

# 2. Safety Rail: Deactivate any user (except other Admins)
@router.patch("/users/{user_id}/deactivate", include_in_schema=True)
async def admin_deactivate_user(
    user_id: int,
    db: AsyncSession = Depends(get_async_db),
    admin: User = Depends(get_superuser),
):
    result = await db.execute(select(User).where(User.id == user_id))
    target_user = result.scalars().first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    # RULE: Cannot deactivate yourself
    if target_user.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate your own admin account. Demote yourself first.")
    # RULE: Admin Wars Protection (Horizontal Blocking)
    if target_user.is_superuser:
        raise HTTPException(status_code=403, detail="Cannot deactivate another superuser")
    
    await db.execute(
    update(Service).where(Service.owner_id == target_user.id).values(is_active=False)
    )

    await db.execute(
        update(Booking)
        .where((Booking.user_id==target_user.id)|(Booking.service_id.in_(select(Service.id)
        .where(Service.owner_id == target_user.id))))
        .values(status="cancelled")
        )
    target_user.is_active = False
    await db.commit()
    return {"detail": f"User {user_id} has been suspended."}

# 3. Hard Delete (Only for already deactivated non-admins)
@router.delete("/users/{user_id}", include_in_schema=True)
async def admin_hard_delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_async_db),
    admin: User = Depends(get_superuser),
):
    result = await db.execute(select(User).where(User.id == user_id))
    target_user = result.scalars().first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    if target_user.is_active:
        raise HTTPException(status_code=400, detail="Only deactivated accounts can be permanently deleted.")

    if target_user.is_superuser:
        raise HTTPException(status_code=403, detail="Superusers cannot be deleted via API.")

    await db.delete(target_user)
    await db.commit()
    return {"detail": "Record permanently removed from database."}

# 4. Content Moderation: Suspend a Service
@router.patch("/services/{service_id}/suspend", include_in_schema=True)
async def admin_suspend_service(
    service_id: int,
    db: AsyncSession = Depends(get_async_db),
    admin: User = Depends(get_superuser),
):
    result = await db.execute(select(Service).where(Service.id == service_id))
    service = result.scalars().first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    service.is_active = False
    await db.commit()
    return {"detail": "Service suspended for review."}
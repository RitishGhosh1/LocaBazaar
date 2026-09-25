from fastapi import APIRouter
from app.api.v1.endpoints import bookings, customers, categories, providers, services, reviews, auth, admin, uploads

api_router = APIRouter()
api_router.include_router(providers.router)
api_router.include_router(services.router)
api_router.include_router(bookings.router)
api_router.include_router(customers.router)
api_router.include_router(auth.router)
api_router.include_router(admin.router)
api_router.include_router(categories.router)
api_router.include_router(reviews.router)
api_router.include_router(uploads.router)
from fastapi import FastAPI
from app.api.v1.api import api_router
from app.models.base import Base 
# Ensure your models are imported here so that they are registered with SQLAlchemy
from app.models.user import User
from app.models.services import Service
from app.models.booking import Booking 
from app.db.session import engine

# This creates the tables on startup if they don't exist
Base.metadata.create_all(bind=engine)

app = FastAPI(title="ProLink API", version="1.0.0")
app.include_router(api_router, prefix="/api/v1")



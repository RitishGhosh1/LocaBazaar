from fastapi import FastAPI
from app.api.v1.api import api_router
from app.models.base import Base 
# Ensure your models are imported here so that they are registered with SQLAlchemy
from app.models.user import User
from app.models.services import Service
from app.models.booking import Booking 
from app.db.session import engine
from app.core.config import token_settings

from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI(title="ProLink API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], # Your Next.js port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    SessionMiddleware,
    secret_key=token_settings.SECRET_KEY
)

# This creates the tables on startup if they don't exist
Base.metadata.create_all(bind=engine)

app.include_router(api_router, prefix="/api/v1")

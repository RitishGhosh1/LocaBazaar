from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from starlette.middleware.sessions import SessionMiddleware
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.rabbitmq import rabbitmq_manager
# Import core routing maps
from app.api.v1.api import api_router

# Ensure your models are imported here so that they are registered with SQLAlchemy
from app.models.base import Base
from app.models.user import User
from app.models.services import Service
from app.models.booking import Booking 
from app.models.uploads import Upload
from app.db.session import engine
from app.core.config import config, token_settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    await rabbitmq_manager.connect()
    yield
    await rabbitmq_manager.close()

# 1. INITIALIZE THE FASTAPI APP WITHOUT THE HARDCODED OAUTH DICTIONARY
# We completely strip out `swagger_ui_init_oauth`. 
# This forces the Swagger UI padlock to request an explicit Client ID input box from the user.
app = FastAPI(
    title="LocaBazaar API", 
    version="1.0.0",
    description="Decoupled Standalone API Platform supporting Native and Dynamic Google OAuth Flows",
    lifespan=lifespan
)

origins = [
    origin.strip().rstrip("/")
    for origin in (config.CORS_ORIGINS or config.FRONTEND_URL).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],                      
    allow_headers=["*"],                      
)

app.add_middleware(
    SessionMiddleware,
    secret_key=token_settings.SECRET_KEY,
    https_only=config.FRONTEND_URL.startswith("https://"),
)

# 2. OVERRIDE OPENAPI LAYER TO ENFORCE EXPLICIT INPUT PARAMETERS
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # We define the flows under the components configuration matrix
    openapi_schema["components"]["securitySchemes"] = {
        "OAuth2PasswordFlow": {
            "type": "oauth2",
            "description": "Enter your email (as username) and password to authenticate natively via form data.",
            "flows": {
                "password": {
                    "tokenUrl": "/api/v1/auth/login",  # Targets your exact native POST /login path [cite: 394]
                    "scopes": {}
                }
            }
        },
        "GoogleSign-In": {
            "type": "oauth2",
            "description": "DYNAMIC GOOGLE AUTH: Paste your unique Google Client ID in the field below to connect.",
            "flows": {
                # Implicit token flow prompts the user for their Client ID value before passing to Google
                "implicit": {
                    "authorizationUrl": "https://accounts.google.com/o/oauth2/v2/auth",
                    "scopes": {
                        "openid": "Required for OpenID Connect mapping",
                        "email": "Access your primary email address",
                        "profile": "Access your public Google profile information"
                    }
                }
            }
        }
    }
    
    # Map global security overrides across your API schema specifications
    openapi_schema["security"] = [
        {"OAuth2PasswordFlow": []},
        {"GoogleSign-In": ["openid", "email", "profile"]}
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Ensure uploads directory exists and mount static files
import os
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

upload_dir = os.path.join(os.getcwd(), "uploads")
os.makedirs(upload_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=upload_dir), name="uploads")

# This creates the tables on startup if they don't exist
Base.metadata.create_all(bind=engine)

# Backward-compatible column migration for existing tables
try:
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE reviews ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();"))
        conn.execute(text("ALTER TABLE reviews ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url VARCHAR;"))
        conn.execute(text("ALTER TABLE services ADD COLUMN IF NOT EXISTS image_url VARCHAR;"))
        conn.commit()
except Exception:
    pass

app.include_router(api_router, prefix="/api/v1")

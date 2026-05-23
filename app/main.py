from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from starlette.middleware.sessions import SessionMiddleware
import os

# Hardened .env fallback parsing to prevent empty environment variables
from pydantic_settings import BaseSettings

# Import core routing maps
from app.api.v1.api import api_router

# Ensure your models are imported here so that they are registered with SQLAlchemy
from app.models.base import Base
from app.models.user import User
from app.models.services import Service
from app.models.booking import Booking 
from app.db.session import engine
from app.core.config import token_settings

# Initialize the FastAPI App instance
# This cleanly links your system variables straight to the Swagger padlock context UI
app = FastAPI(
    title="LocaBazaar API", 
    version="1.0.0",
    description="Standalone Universal API Platform - complete Documentation Hub",
    swagger_ui_init_oauth={
        "clientId": os.getenv("GOOGLE_CLIENT_ID"), # Dynamically reads your local environment parameter
        "appName": "LocaBazaar",
        "scopes": ["openid", "email", "profile"]
    }
)

origins = [
    "*",  # Open platform decoupling wildcard configuration allowance
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
    secret_key=token_settings.SECRET_KEY
)

# Overriding the default OpenAPI schema generation to inject both Security Schemes side-by-side
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # We mount your standard email/password form alongside your structural Google flow
    openapi_schema["components"]["securitySchemes"] = {
        "OAuth2PasswordFlow": {
            "type": "oauth2",
            "description": "Enter your email (as username) and password to authenticate natively via form data.",
            "flows": {
                "password": {
                    "tokenUrl": "/api/v1/auth/login",  # Targets your exact native token exchange endpoint path
                    "scopes": {}
                }
            }
        },
        "GoogleSign-In": {
            "type": "oauth2",
            "description": "One-Click native Google sign-in wrapper for Swagger UI testing.",
            "flows": {
                # Implicit routing delivers the token directly into Swagger's secure internal state session
                "implicit": {
                    "authorizationUrl": "https://accounts.google.com/o/oauth2/v2/auth", # ALWAYS TARGET GOOGLE DIRECTLY
                    "scopes": {
                        "openid": "Required for OpenID Connect mapping access tokens",
                        "email": "Access your primary email address parameter profile",
                        "profile": "Access your public Google directory data profile claims"
                    }
                }
            }
        }
    }
    
    # Configure global application security dependencies
    openapi_schema["security"] = [
        {"OAuth2PasswordFlow": []},
        {"GoogleSign-In": ["openid", "email", "profile"]}
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# This creates the tables on startup if they don't exist
Base.metadata.create_all(bind=engine)

app.include_router(api_router, prefix="/api/v1")
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from starlette.middleware.sessions import SessionMiddleware

# Import core routing maps
from app.api.v1.api import api_router

# Ensure your models are imported here so that they are registered with SQLAlchemy
from app.models.base import Base
from app.models.user import User
from app.models.services import Service
from app.models.booking import Booking 
from app.db.session import engine
from app.core.config import token_settings

# 1. INITIALIZE THE FASTAPI APP WITHOUT THE HARDCODED OAUTH DICTIONARY
# We completely strip out `swagger_ui_init_oauth`. 
# This forces the Swagger UI padlock to request an explicit Client ID input box from the user.
app = FastAPI(
    title="LocaBazaar API", 
    version="1.0.0",
    description="Decoupled Standalone API Platform supporting Native and Dynamic Google OAuth Flows"
)

origins = [
    "*",  # Universal open platform allowance for API consumers
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

# This creates the tables on startup if they don't exist
Base.metadata.create_all(bind=engine)

app.include_router(api_router, prefix="/api/v1")
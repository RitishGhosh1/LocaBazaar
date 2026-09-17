import jwt
from datetime import datetime, timedelta, timezone

from app.core.config import token_settings



def generate_verification_token(email: str) -> str:
    now = datetime.now(timezone.utc)

    payload = {
        "sub": email,
        "type": "email_verification",
        "iat": now,
        "exp": now + timedelta(
            minutes=token_settings.ACCESS_TOKEN_EXPIRE_MINUTES
        ),
    }

    return jwt.encode(
        payload,
        token_settings.SECRET_KEY,
        algorithm=token_settings.ALGORITHM,
    )


def verify_verification_token(token: str) -> str | None:
    try:
        payload = jwt.decode(
            token,
            token_settings.SECRET_KEY,
            algorithms=[token_settings.ALGORITHM],
        )

        if payload.get("type") != "email_verification":
            return None

        email = payload.get("sub")

        if not email:
            return None

        return email

    except jwt.ExpiredSignatureError:
        return None

    except jwt.InvalidTokenError:
        return None
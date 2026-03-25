import jwt
from datetime import datetime, timedelta, timezone
from .config import token_settings

SECRET_KEY = token_settings.SECRET_KEY
ALGORITHM = token_settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = token_settings.ACCESS_TOKEN_EXPIRE_MINUTES

import bcrypt

def get_password_hash(password: str) -> str:
    # 1. Convert string to bytes
    pwd_bytes = password.encode('utf-8')
    # 2. Generate a salt
    salt = bcrypt.gensalt()
    # 3. Hash the password
    hashed_password = bcrypt.hashpw(pwd_bytes, salt)
    # 4. Return as a decodeable string for the DB
    return hashed_password.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode=data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc)+ expires_delta
    else:
        expire=datetime.now(timezone.utc)+ timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt=jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


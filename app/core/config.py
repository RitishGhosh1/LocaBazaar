from pydantic_settings import BaseSettings, SettingsConfigDict

class Config(BaseSettings):
    DB_USER: str
    DB_NAME: str
    DB_HOST: str
    DB_PORT: int
    DB_PASSWORD: str
    
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    
    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None
    GOOGLE_CONF_URL: str = "https://accounts.google.com/.well-known/openid-configuration"
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8",extra="ignore")

config=Config()

class TokenSettings(BaseSettings):
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8",extra="ignore")
token_settings = TokenSettings()
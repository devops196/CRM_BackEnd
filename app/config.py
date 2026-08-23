from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PORT: int = 8000
    NODE_ENV: str = "development"
    FRONTEND_URL: str = "http://localhost:5173"
    JWT_SECRET: str
    JWT_EXPIRES_IN: str = "7d"
    COOKIE_NAME: str = "access_token"
    DATABASE_URL: str
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()

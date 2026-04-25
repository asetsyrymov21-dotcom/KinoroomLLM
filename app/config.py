from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/kinorum"
    DB_ECHO: bool = False

    # JWT
    SECRET_KEY: str = "kinorum-secret-key-change-in-production"
    TOKEN_EXPIRE_HOURS: int = 24 * 7  # 7 дней

    # Superadmin (нет записи в БД — аутентификация только через env)
    SUPERADMIN_USERNAME: str = "superadmin"
    SUPERADMIN_PASSWORD: str = "change-me-in-production"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

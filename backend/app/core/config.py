from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "BoviCare AI API"
    environment: str = "development"
    database_url: str = "sqlite:///./bovicare.db"
    secret_key: str = "development-only-change-me"
    access_token_expire_minutes: int = 1440
    jwt_algorithm: str = "HS256"
    frontend_origins: str = "http://localhost:5173"
    upload_dir: str = "./private_uploads"
    max_image_size: int = 10 * 1024 * 1024
    notification_provider: str = "mock"
    notification_email_api_key: str | None = None
    notification_sms_api_key: str | None = None
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    def validate_runtime_security(self) -> None:
        if self.environment.lower() in {"production", "prod"} and self.secret_key == "development-only-change-me":
            raise RuntimeError("SECRET_KEY must be changed before running in production.")

    @property
    def origins(self) -> list[str]:
        return [origin.strip() for origin in self.frontend_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

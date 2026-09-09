from typing import Any, List
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Committed development-only key. Safe for local work, never for a deployment --
# see _reject_insecure_production_config below.
DEV_SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"


class Settings(BaseSettings):
    PROJECT_NAME: str = "AUSA - AI University & Scholarship Advisor"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, v: Any) -> bool:
        if isinstance(v, str):
            if v.lower() in {"release", "prod", "production", "0", "false", "no", "off"}:
                return False
            if v.lower() in {"debug", "dev", "development", "1", "true", "yes", "on"}:
                return True
        return bool(v)

    # JWT Authentication Security
    SECRET_KEY: str = Field(
        default=DEV_SECRET_KEY,
        description="JWT Secret Key for Token Signatures. MUST be overridden outside development."
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Administrator allowlist. Empty means nobody is an administrator -- an
    # unconfigured deployment must be a closed one, not an open one.
    ADMIN_EMAILS: List[str] = Field(
        default_factory=list,
        description="Emails permitted to use /api/v1/admin. Empty denies everyone.",
    )

    # Database
    POSTGRES_USER: str = "ausa_user"
    POSTGRES_PASSWORD: str = "ausa_password"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "ausa_db"
    
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://ausa_user:ausa_password@localhost:5432/ausa_db",
        description="Async PostgreSQL Database Connection String"
    )
    
    # CORS -- exact origins only. Never "*": the API is mounted with
    # allow_credentials=True, and a wildcard there lets any site read a
    # logged-in user's data. Add deployed frontend origins via the env var.
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # Authorisation allowlist for /api/v1/admin/* (data verification, seeding).
    # Fail-closed: empty means nobody is an admin. Set via the ADMIN_EMAILS env var.
    ADMIN_EMAILS: List[str] = []

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @model_validator(mode="after")
    def _reject_insecure_production_config(self) -> "Settings":
        """Refuse to boot a production deployment with development defaults.

        The default SECRET_KEY is committed to the repository, so anything using
        it can have its JWTs forged by anyone who has read the source. Failing at
        startup is much cheaper than discovering this in production.
        """
        if self.ENVIRONMENT.strip().lower() not in {"production", "prod"}:
            return self

        if self.SECRET_KEY == DEV_SECRET_KEY:
            raise ValueError(
                "SECRET_KEY is still the committed development default. "
                "Set a unique SECRET_KEY environment variable before deploying."
            )
        if "*" in self.BACKEND_CORS_ORIGINS:
            raise ValueError(
                "BACKEND_CORS_ORIGINS contains '*', which is unsafe with "
                "allow_credentials=True. List exact frontend origins instead."
            )
        return self


settings = Settings()

import os
from dataclasses import dataclass, field
from os import urandom
from pathlib import Path

from advanced_alchemy.base import orm_registry
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.schema import MetaData

TRUE_VALUES = {"True", "true", "1", "yes", "Y", "T"}


@dataclass
class DatabaseSettings:
    """Settings for SQLAlchemy and database instantiation"""

    BACKUP: bool = field(
        default_factory=lambda: os.getenv("DATABASE_BACKUP", "True") in TRUE_VALUES
    )
    ECHO: bool = field(default_factory=lambda: os.getenv("DATABASE_ECHO", "False") in TRUE_VALUES)
    URL: str = field(
        default_factory=lambda: os.getenv("DATABASE_URL", "sqlite+aiosqlite:///dev.db")
    )
    ENGINE_DEPENDENCY_KEY: str = field(default="db_engine")
    SESSION_DEPENDENCY_KEY: str = field(default="db_session")
    ENGINE_APP_STATE_DEPENDENCY_KEY: str = field(default="db_engine")
    SESSION_MAKER_CLASS_DEPENDENCY_KEY: str = field(default="session_maker_class")
    """ Whether the database should generate all schema based on SA ORM """
    GENERATE_SCHEMA_ON_INIT: bool = field(default=True)
    """ Uses orm_registry metadata to provide schema information, set according to above ONLY"""
    METADATA_SOURCE: MetaData | None = orm_registry.metadata if GENERATE_SCHEMA_ON_INIT else None

    _engine_instance: AsyncEngine | None = None

    @property
    def engine(self) -> AsyncEngine:
        if self._engine_instance is not None:
            return self._engine_instance
        return self.get_engine()

    def get_engine(self) -> AsyncEngine:
        self._engine_instance = create_async_engine(url=self.URL)
        return self._engine_instance


@dataclass
class TemplateSettings:
    """Settings for serving jinja templates"""

    TEMPLATE_DIR: str = field(default_factory=lambda: os.getenv("TEMPLATE_DIR", "dist/pages"))
    STATIC_DIR: str = field(default_factory=lambda: os.getenv("STATIC_DIR", "dist/static"))
    ASSETS_ENDPOINT: str = field(default="/static")


@dataclass
class ServerSettings:
    """Settings for uvicorn server"""

    APP_LOC: str = "app.app:app"
    HOST: str = field(default_factory=lambda: os.getenv("LITESTAR_HOST", "0.0.0.0"))
    PORT: int = field(default_factory=lambda: int(os.getenv("LITESTAR_PORT", "8000")))
    RELOAD: bool = field(
        default_factory=lambda: os.getenv("LITESTAR_RELOAD", "False") in TRUE_VALUES
    )
    RELOAD_DIRS: list[str] = field(default_factory=lambda: ["src"])


@dataclass
class AppSettings:
    """Application configuration"""

    URL: str = field(default_factory=lambda: os.getenv("APP_URL", "http://localhost:8000"))
    DEBUG: bool = field(default_factory=lambda: os.getenv("LITESTAR_DEBUG", "True") in TRUE_VALUES)
    SECRET_KEY: bytes = field(
        default_factory=lambda: os.getenv("SECRET_KEY", "").encode("utf-8") or urandom(16)
    )
    NAME: str = field(default_factory=lambda: "app")
    AUTHENTICATE: bool = field(default_factory=lambda: os.getenv("TESTING", "True") in TRUE_VALUES)


@dataclass
class CLISettings:
    """CLI running configuration"""

    """ The PARENT folder of app.py """
    APP_DIR: str = field(default="src")


@dataclass
class Settings:
    app: AppSettings = field(default_factory=AppSettings)
    server: ServerSettings = field(default_factory=ServerSettings)
    db: DatabaseSettings = field(default_factory=DatabaseSettings)
    template: TemplateSettings = field(default_factory=TemplateSettings)
    cli: CLISettings = field(default_factory=CLISettings)

    @classmethod
    def from_env(cls, dotenv_filename: str = ".env") -> "Settings":
        from litestar.cli._utils import console

        env_file = Path(os.curdir) / Path(dotenv_filename)
        if env_file.is_file():
            from dotenv import load_dotenv

            console.print(f"[yellow]Loading environment configuration from {dotenv_filename}[/]")

            load_dotenv(env_file)

        return cls()


def get_settings() -> Settings:
    return Settings.from_env()

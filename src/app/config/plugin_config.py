import os
import posixpath
from pathlib import Path
from typing import Any

from advanced_alchemy.extensions.litestar import (
    AsyncSessionConfig,
    SQLAlchemyAsyncConfig,
    async_autocommit_before_send_handler,
)
from click import Command, Context, Group, Option
from jinja2 import Environment, FileSystemLoader
from litestar.connection import ASGIConnection
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.middleware.session.client_side import ClientSideSessionBackend, CookieBackendConfig
from litestar.plugins import CLIPluginProtocol
from litestar.security.session_auth import SessionAuth
from litestar.static_files import create_static_files_router  # type: ignore
from litestar.template.config import TemplateConfig
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain import urls
from app.domain.schema import User
from app.domain.template_filters import (
    format_and_localize_timestamp,
    get_basefile_name,
    reduce_slashes,
    truncate_string,
)

from .base import CLISettings, get_settings

settings = get_settings()

alchemy_config = SQLAlchemyAsyncConfig(
    engine_instance=settings.db.get_engine(),
    before_send_handler=async_autocommit_before_send_handler,
    session_config=AsyncSessionConfig(expire_on_commit=True),
    engine_dependency_key=settings.db.ENGINE_DEPENDENCY_KEY,
    session_dependency_key=settings.db.SESSION_DEPENDENCY_KEY,
    engine_app_state_key=settings.db.ENGINE_APP_STATE_DEPENDENCY_KEY,
    # TODO: add alembic async session config?
)


async def retrieve_user_handler(
    session: dict[str, str], connection: ASGIConnection[Any, Any, Any, Any]
) -> User | None:
    user_id: str = session.get("user_id", "user_id")
    if not user_id:
        return None

    engine = connection.app.state.get(settings.db.ENGINE_DEPENDENCY_KEY)
    async with AsyncSession(engine) as db_session:
        query = select(User).where(User.id == user_id)
        result = await db_session.execute(query)
        return result.scalars().unique().one_or_none()


session_auth = SessionAuth[User, ClientSideSessionBackend](
    retrieve_user_handler=retrieve_user_handler,  # type: ignore
    session_backend_config=CookieBackendConfig(secret=settings.app.SECRET_KEY),
    exclude=[
        urls.LOGIN_PAGE,
        urls.LOGIN_USER,
        urls.CHECK_USERNAME,
        settings.template.ASSETS_ENDPOINT,
        urls.SCHEMA_ENDPOINT,
    ],
)


class RelEnvironment(Environment):
    def join_path(self, template: str, parent: str) -> str:
        return posixpath.join(posixpath.dirname(parent), template)


jinja_env = RelEnvironment(
    loader=FileSystemLoader(settings.template.TEMPLATE_DIR)
)  # NOTE: cannot prefix "/"
jinja_env.filters.update(
    {
        "reduce_slashes": reduce_slashes,
        "filter_timestamp": format_and_localize_timestamp,
        "truncate_string": truncate_string,
        "get_basefile_name": get_basefile_name,
    }
)

template_config = TemplateConfig(instance=JinjaTemplateEngine.from_environment(jinja_env))

static_files_router = create_static_files_router(
    path=settings.template.ASSETS_ENDPOINT,
    directories=[settings.template.STATIC_DIR],
)


class AppDirCLIPlugin(CLIPluginProtocol):
    def __init__(self, settings: CLISettings):
        self.app_dir = Path(settings.APP_DIR).resolve()

    def on_cli_init(self, cli: Group) -> None:
        # Find the 'run' command
        run_command = cli.get_command(Context(cli), "run")
        if not isinstance(run_command, Command):
            return

        # Create a new --app-dir option
        app_dir_option = Option(
            ["--app-dir"],
            default=str(self.app_dir),
            help="Specify the application directory.",
            show_default=True,
        )

        # Add the option to the run command
        run_command.params.append(app_dir_option)

        # Wrap the run command's callback
        original_callback = run_command.callback

        def wrapped_callback(*args, **kwargs):
            app_dir: str | None = kwargs.pop("app_dir", None)
            if app_dir:
                os.environ["LITESTAR_APP_DIR"] = app_dir
            return original_callback(*args, **kwargs)

        run_command.callback = wrapped_callback

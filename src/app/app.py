from os import urandom
from typing import Any, Dict

from advanced_alchemy.base import orm_registry

# from advanced_alchemy.config import EngineConfig
from advanced_alchemy.config.asyncio import AsyncSessionConfig
from advanced_alchemy.extensions.litestar.plugins.init.config.asyncio import (
    autocommit_before_send_handler,
)
from jinja2 import Environment, FileSystemLoader
from litestar import Litestar
from litestar.connection import ASGIConnection
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.contrib.sqlalchemy.plugins import SQLAlchemyAsyncConfig, SQLAlchemyPlugin
from litestar.middleware.session.client_side import ClientSideSessionBackend, CookieBackendConfig
from litestar.security.session_auth import SessionAuth
from litestar.static_files import create_static_files_router  # type: ignore
from litestar.template.config import TemplateConfig
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.domain import urls
from app.domain.controllers import PageController, SystemController, TaskController, UserController
from app.domain.schema import User
from app.domain.template_filters import (
    format_and_localize_timestamp,
    reduce_slashes,
    truncate_string,
)

db_config = SQLAlchemyAsyncConfig(
    connection_string="sqlite+aiosqlite:///dev.db",
    metadata=orm_registry.metadata,
    create_all=True,
    before_send_handler=autocommit_before_send_handler,
    session_config=AsyncSessionConfig(expire_on_commit=True),
)


async def retrieve_user_handler(
    session: Dict[str, Any], connection: ASGIConnection[Any, Any, Any, Any]
) -> User | None:
    user_id = session.get("user_id")
    if not user_id:
        return None

    engine = connection.app.state.get("engine")
    if engine is None:
        engine = create_async_engine("sqlite+aiosqlite:///dev.db")
        connection.app.state.engine = engine

    async with AsyncSession(engine) as db_session:
        query = select(User).where(User.id == user_id)
        result = await db_session.execute(query)
        return result.scalars().unique().one_or_none()


session_auth = SessionAuth[User, ClientSideSessionBackend](
    retrieve_user_handler=retrieve_user_handler,  # type: ignore
    session_backend_config=CookieBackendConfig(secret=urandom(16)),
    exclude=[
        urls.LOGIN_PAGE,
        urls.LOGIN_USER,
        urls.CHECK_USERNAME,
        urls.ASSETS_ENDPOINT,
        urls.SCHEMA_ENDPOINT,
    ],
)

jinja_env = Environment(loader=FileSystemLoader("dist/pages"))  # NOTE: cannot prefix "/"
jinja_env.filters.update(
    {
        "reduce_slashes": reduce_slashes,
        "filter_timestamp": format_and_localize_timestamp,
        "truncate_string": truncate_string,
    }
)

# async def on_startup() -> None:
#     """Initializes the database."""
#     async with db_config.get_engine().begin() as conn:
#         await conn.run_sync(Base.metadata.create_all)

webpack_bundle_router = create_static_files_router(
    path=urls.ASSETS_ENDPOINT,
    directories=["dist/static"],
)

app = Litestar(
    # route_handlers=[PageController, UserController, panel_page, check_username, create_new_user,
    #                 get_task_profile_picture, get_task_keybinds, label_update_annotation,
    #                 label_undo_annotation, label_page, label_get_next_image, label_get_image,
    #                 create_static_files_router(path="static", directories=["static"])],
    route_handlers=[
        PageController,
        UserController,
        SystemController,
        TaskController,
        webpack_bundle_router,
    ],
    template_config=TemplateConfig(instance=JinjaTemplateEngine.from_environment(jinja_env)),
    # on_startup=[on_startup],
    # dependencies={"transaction": provide_transaction},
    plugins=[SQLAlchemyPlugin(db_config)],
    on_app_init=[session_auth.on_app_init],
    middleware=[session_auth.middleware],
)

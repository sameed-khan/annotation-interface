from collections.abc import AsyncGenerator, AsyncIterator, Generator
from pathlib import Path
from uuid import UUID

import pytest
from advanced_alchemy.base import orm_registry
from advanced_alchemy.utils.fixtures import open_fixture_async
from app.config import base
from app.domain.schema import Task, User
from app.domain.services import AnnotationService, LabelKeybindService, TaskService, UserService
from fixture_options import FIXTURE_OPTIONS
from generate_fixtures import generate_fixtures, teardown_fixtures
from litestar import Litestar
from litestar.testing import AsyncTestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

pytestmark = pytest.mark.anyio
pytest_plugins = ["app_fixture"]
settings = base.get_settings()


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--teardown-fixtures",
        action="store_true",
        default=False,
        help="Tear down fixtures after tests. Regenerating fixtures on next run takes time.",
    )


@pytest.fixture(scope="session", autouse=True)
def setup(request: pytest.FixtureRequest) -> Generator[None, None, None]:
    generate_fixtures()

    yield
    if request.config.getoption("--teardown-fixtures"):
        print("Tearing down fixtures")
        teardown_fixtures()


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(name="test_user")
def fx_test_user() -> dict[str, str | int | float]:
    return FIXTURE_OPTIONS.test_user


@pytest.fixture(name="test_task")
def fx_test_task() -> dict[str, str]:
    return FIXTURE_OPTIONS.test_task


# @pytest.fixture(autouse=True)
# def _patch_auth(monkeypatch: pytest.MonkeyPatch) -> None:
#     """Patch the ClientSideSessionBackend to stop using encryption for its cookies"""

#     def mock_dump_data(self, data: Any, scope: Scope | None = None) -> list[bytes]:
#         json_data = mjson.encode(data)
#         return [b64encode(json_data)]

#     def mock_load_data(self, data: Any):
#         json_data = b64decode(b"".join(data))
#         return mjson.decode(json_data)

#     monkeypatch.setattr(ClientSideSessionBackend, "dump_data", mock_dump_data)
#     monkeypatch.setattr(ClientSideSessionBackend, "load_data", mock_load_data)


@pytest.fixture(autouse=True)
def _patch_client(  # type: ignore
    client: AsyncTestClient[Litestar],
    engine: AsyncEngine,
    sessionmaker: async_sessionmaker[AsyncSession],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(client.app.state, settings.db.ENGINE_DEPENDENCY_KEY, engine)
    monkeypatch.setitem(
        client.app.state, settings.db.SESSION_MAKER_CLASS_DEPENDENCY_KEY, sessionmaker
    )


@pytest.fixture(name="engine", autouse=True)
def fx_engine() -> AsyncEngine:
    """Creates async sql engine"""
    return create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )


@pytest.fixture(name="sessionmaker")
def fx_session_maker_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(bind=engine, expire_on_commit=False)


@pytest.fixture(name="session")
async def fx_session(
    sessionmaker: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession, None]:
    async with sessionmaker() as session:
        yield session


@pytest.fixture(autouse=True)
async def _seed_db(  # type: ignore
    engine: AsyncEngine,
    sessionmaker: async_sessionmaker[AsyncSession],
) -> AsyncIterator[None]:
    fixtures_path = Path(FIXTURE_OPTIONS.fixtures_folder).resolve()
    metadata = orm_registry.metadata
    async with engine.begin() as conn:
        await conn.run_sync(metadata.drop_all)
        await conn.run_sync(metadata.create_all)
    async with UserService.new(sessionmaker()) as users_service:
        user_data = await open_fixture_async(fixtures_path, "users")
        await users_service.create_many(user_data, auto_commit=True)  # user many to many tasks
    async with TaskService.new(sessionmaker()) as tasks_service:
        task_data = await open_fixture_async(fixtures_path, "tasks")
        await tasks_service.create_many(task_data, auto_commit=True)  # task one to many anno, lk
    async with LabelKeybindService.new(sessionmaker()) as lks_service:
        lks_data = await open_fixture_async(fixtures_path, "label_keybinds")
        await lks_service.create_many(lks_data, auto_commit=True)  # no downstream deps
    async with AnnotationService.new(sessionmaker()) as annos_service:
        annos_data = await open_fixture_async(fixtures_path, "annotations")
        await annos_service.create_many(annos_data, auto_commit=True)  # no downstream deps

    async with sessionmaker() as session:
        user_tasks_assoc_table = await open_fixture_async(fixtures_path, "user_tasks")
        for user_task_dict in user_tasks_assoc_table:
            user_id, task_id = list(user_task_dict.items())[0]
            user = (
                await session.execute(select(User).where(User.id == UUID(user_id)))
            ).scalar_one()
            task = (
                await session.execute(select(Task).where(Task.id == UUID(task_id)))
            ).scalar_one()

            user.assigned_tasks.append(task)
            await session.commit()

    yield

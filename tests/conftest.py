from collections.abc import AsyncGenerator, AsyncIterator, Generator
from pathlib import Path

import pytest
from advanced_alchemy.base import orm_registry
from advanced_alchemy.utils.fixtures import open_fixture_async
from fixture_options import FIXTURE_OPTIONS
from generate_fixtures import generate_fixtures, teardown_fixtures
from litestar import Litestar
from litestar.testing import AsyncTestClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.app import app
from app.domain.services import AnnotationService, LabelKeybindService, TaskService, UserService


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--teardown-fixtures",
        action="store_true",
        default=False,
        help="Tear down fixtures after testing session completed",
    )


@pytest.fixture(scope="session", autouse=True)
def setup(request: pytest.FixtureRequest) -> Generator[None, None, None]:
    generate_fixtures()

    yield
    if request.config.getoption("--teardown-fixtures"):
        print("Tearing down fixtures")
        teardown_fixtures()


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(name="client")
async def fx_client() -> AsyncIterator[AsyncTestClient[Litestar]]:
    async with AsyncTestClient(app=app, base_url="http://testserver.local") as client:
        yield client


@pytest.fixture(name="engine", autouse=True)
async def fx_engine() -> AsyncEngine:
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
        await users_service.create_many(user_data, auto_commit=True)
    async with TaskService.new(sessionmaker()) as tasks_service:
        task_data = await open_fixture_async(fixtures_path, "tasks")
        await tasks_service.create_many(task_data, auto_commit=True)
    async with LabelKeybindService.new(sessionmaker()) as lks_service:
        lks_data = await open_fixture_async(fixtures_path, "label_keybinds")
        await lks_service.create_many(lks_data, auto_commit=True)
    async with AnnotationService.new(sessionmaker()) as annos_service:
        annos_data = await open_fixture_async(fixtures_path, "annotations")
        await annos_service.create_many(annos_data, auto_commit=True)

    yield


@pytest.fixture(autouse=True)
def _patch_db(  # type: ignore
    client: AsyncTestClient[
        Litestar
    ],  # TODO: generate app distance from a fixture using create_app function
    engine: AsyncEngine,
    sessionmaker: async_sessionmaker[AsyncSession],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # TODO: get the keys dynamically from app.py or another config file that
    # sets those keys / values
    monkeypatch.setitem(client.app.state, "db_engine", engine)
    monkeypatch.setitem(client.app.state, "session_maker_class", sessionmaker)

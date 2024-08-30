from collections.abc import AsyncGenerator
from typing import Any

import pytest
from advanced_alchemy.extensions.litestar.plugins import SQLAlchemyPlugin
from app.config import base, get_settings
from app.config.plugin_config import (
    AppDirCLIPlugin,
    alchemy_config,
    session_auth,
    static_files_router,
    template_config,
)
from app.domain.controllers import (
    AnnotationController,
    PageController,
    SystemController,
    TaskController,
    UserController,
)
from litestar import Litestar
from litestar.middleware.session.client_side import CookieBackendConfig
from litestar.testing import AsyncTestClient, create_async_test_client

pytestmark = pytest.mark.anyio


@pytest.fixture(name="client")
async def fx_client(
    test_user: dict[str, str | int | float],
) -> AsyncGenerator[AsyncTestClient[Litestar], Any]:
    settings = get_settings()
    client_session_config = CookieBackendConfig(secret=settings.app.SECRET_KEY)

    async with create_async_test_client(
        route_handlers=[
            PageController,
            UserController,
            SystemController,
            TaskController,
            AnnotationController,
            static_files_router,
        ],
        plugins=[SQLAlchemyPlugin(alchemy_config), AppDirCLIPlugin(settings.cli)],
        template_config=template_config,
        on_app_init=[session_auth.on_app_init],
        middleware=[session_auth.middleware],
        session_config=client_session_config,
        raise_server_exceptions=True,
    ) as client:
        await client.set_session_data({"user_id": test_user["id"]})
        yield client


@pytest.fixture(autouse=True)
def _patch_backend(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    A terrible, horrible hack that I hate implementing but don't have the time to get to the root
    cause of the issue.
    When self.client.post request is made with AsyncTestClient, it does not use the
    CookieBackendConfig defined by the app settings in plugin_config.py - rather it uses some other
    set of potential default settings to create a new instance of the ClientSideSessionBackend
    (also might be a new instance of the Litestar app, not sure).
    This new instance is created IN BETWEEN the encryption of session data with the testing-spec
    secret key ('ababomangravwind') and whatever default secret key it comes up with -- so
    decryption fails and the session data gets returned as an empty dictionary.

    Solution: mock the AESGCM encryption cipher class used in ClientSideSessionBackend
    directly to always have the same secret key as we specified in our settings.
    """
    from cryptography import utils
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    settings = get_settings()

    def new_init(self: AESGCM, key: bytes):
        utils._check_byteslike("key", key)  # type: ignore
        if len(key) not in (16, 24, 32):
            raise ValueError("AESGCM key must be 128, 192, or 256 bits.")

        self._key = settings.app.SECRET_KEY  # type: ignore

    monkeypatch.setattr(AESGCM, "__init__", new_init)


@pytest.fixture(autouse=True)
def _patch_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """Patch the settings"""
    settings = base.Settings.from_env(".env.testing")

    def get_settings(dotenv_filename: str = ".env.testing") -> base.Settings:
        return settings

    monkeypatch.setattr(base, "get_settings", get_settings)


# @pytest.fixture(name="app")
# def fx_app() -> Litestar:
#     return create_app()


# @pytest.fixture(name="client")
# async def fx_client(
#     app: Litestar,
#     test_user: dict[str, str | int | float],
# ) -> AsyncIterator[AsyncTestClient[Litestar]]:
#     _json = json.dumps(test_user)
#     async with AsyncTestClient(
#         app=app,
#         base_url="http://testserver.local",
#         session_config=session_auth.session_backend_config,
#         cookies={"session": _json},
#     ) as client:
#         await client.set_session_data({"user_id": test_user["id"]})
#         yield client

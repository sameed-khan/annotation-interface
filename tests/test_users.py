import json
from base64 import b64decode
from typing import Any, Dict, Literal

import pytest
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from litestar import Litestar
from litestar.status_codes import HTTP_200_OK, HTTP_201_CREATED, HTTP_401_UNAUTHORIZED
from litestar.testing import AsyncTestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain import urls
from app.domain.schema import User

pytestmark = pytest.mark.anyio


def helper_decode_string(encoded: str, secret_key: bytes) -> Dict[str, Any]:
    """Decode secret session data according to library code of ClientSideSessionBackend"""
    nonce_size = 12
    aad = b"additional_authenticated_data="
    cipher = AESGCM(secret_key)
    encoded = encoded.strip("'\"")
    decoded = b64decode(encoded)
    nonce = decoded[:nonce_size]
    aad_starts_from = decoded.find(aad)
    associated_data = decoded[aad_starts_from:].replace(aad, b"")
    encrypted = decoded[nonce_size:aad_starts_from]
    decrypted = cipher.decrypt(nonce, encrypted, associated_data=associated_data)
    decrypted_as_string = decrypted.decode("utf-8")

    return json.loads(decrypted_as_string)


@pytest.mark.parametrize(
    "username,password,expected_status,check_cookie",
    [
        ("captain_ababo", "gravenwind", HTTP_200_OK, True),
        ("invalid_user", "invalid_password", HTTP_401_UNAUTHORIZED, False),
    ],
)
async def test_login(
    client: AsyncTestClient[Litestar],
    username: str,
    password: str,
    expected_status: Literal[200, 401],
    check_cookie: bool,
):
    response = await client.post(
        urls.LOGIN_USER,
        json={"request_username": username, "request_password": password},
    )
    assert response.status_code == expected_status

    if check_cookie:
        assert "session" in response.cookies
        secret: bytes = client.app.middleware[-1].kwargs["config"].session_backend_config.secret  # type: ignore
        session = helper_decode_string(response.cookies["session"], secret)  # type: ignore
        assert "user_id" in session


async def test_create_user(client: AsyncTestClient[Litestar], session: AsyncSession):
    # TODO: refactor user request and receive as DTO
    response = await client.post(
        urls.CREATE_USER,
        json={"request_username": "new_user", "request_password": "new_password"},
    )
    result = await session.execute(select(User).where(User.username == "new_user"))
    user = result.scalar_one_or_none()

    jsonified = response.json()
    response_id, response_username = jsonified["id"], jsonified["username"]

    assert response.status_code == HTTP_201_CREATED

    assert user is not None
    assert user.username == "new_user"
    assert user.password == "new_password"

    assert response_id == str(user.id)
    assert response_username == user.username

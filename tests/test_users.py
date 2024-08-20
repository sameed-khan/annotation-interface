import json
from base64 import b64decode
from typing import Any, Dict, Literal

import pytest
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from litestar import Litestar
from litestar.status_codes import HTTP_200_OK, HTTP_401_UNAUTHORIZED
from litestar.testing import AsyncTestClient

from app.domain import urls

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

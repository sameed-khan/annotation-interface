import json
from base64 import b64decode
from typing import Any, Literal
from uuid import UUID

import pytest
from app.domain import urls
from app.domain.constants import DEFAULT_KEYBINDS_IN_ORDER
from app.domain.schema import User
from app.domain.services import TaskService, UserService
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from litestar import Litestar
from litestar.status_codes import HTTP_200_OK, HTTP_201_CREATED, HTTP_401_UNAUTHORIZED
from litestar.testing import AsyncTestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

pytestmark = pytest.mark.anyio


def helper_decode_string(encoded: str, secret_key: bytes) -> dict[str, Any]:
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

    if check_cookie:
        secret: bytes = client.app.middleware[-1].kwargs["config"].session_backend_config.secret  # type: ignore
        session = helper_decode_string(response.cookies["session"], secret)  # type: ignore
        assert "session" in response.cookies
        assert "user_id" in session

    assert response.status_code == expected_status


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


async def test_assign_user_task(
    client: AsyncTestClient[Litestar],
    test_user: dict[str, str | int | float],
    test_task: dict[str, str | int | float],
    sessionmaker: async_sessionmaker[AsyncSession],
):
    """Test business logic after assigning user to task"""
    async with TaskService.new(sessionmaker()) as tasks_service:
        temp = await tasks_service.get_all_tasks()
        some_old_tasks = [task for task in temp if task.id != UUID(test_task["id"])][:3]  # type: ignore

    snt_ids = [str(task.id) for task in some_old_tasks]

    response = await client.post(
        urls.ASSIGN_TASK, json={"tasks_to_add_ids": [_id for _id in snt_ids]}
    )

    async with TaskService.new(sessionmaker()) as tasks_service:
        updated_tasks = await tasks_service.get_many_by_id([_id for _id in snt_ids])

    async with UserService.new(sessionmaker()) as users_service:
        updated_user = await users_service.get_one(id=UUID(test_user["id"]))  # type: ignore

    for updated_task in updated_tasks:
        labelset = list(set([lk.label for lk in updated_task.label_keybinds]))
        user_lks = [
            lk for lk in updated_user.label_keybinds if str(lk.task_id) == str(updated_task.id)
        ]
        user_labelset = [lk.label for lk in user_lks]
        user_keybinds = [lk.keybind for lk in user_lks]

        # user label that are default generated should cover the entire set of labels
        assert user_labelset == labelset, f"user_labelset: {user_labelset}; labelset: {labelset}"

        # user keybinds should be in order of default generated
        # Ex:
        #   label_keybinds: {"label1": "f", "label2": "g", "label3": i}
        #   user_generated_keybinds: "a", "s" -- since two labels
        assert user_keybinds == DEFAULT_KEYBINDS_IN_ORDER[: len(labelset)]

    assert response.status_code == HTTP_200_OK


async def test_unassign_user_from_task(
    client: AsyncTestClient[Litestar],
    test_user: dict[str, str | int | float],
    test_task: dict[str, str | int | float],
    sessionmaker: async_sessionmaker[AsyncSession],
):
    """
    Test business logic for unassigning user from task
    Removing a user from task should:
    - remove the task from user's list of assigned tasks
    - check whether user label keybind is not deleted
    - check whether task label keybind is not deleted
    - ^^ ensures that keybinds are there again if the task is reassigned
    """
    # Ideally would not have to do act-arrange-assert but need to in order to view database updates
    async with UserService.new(sessionmaker()) as users_service:
        old_user = await users_service.get_one(id=test_user["id"])  # type: ignore
        old_user_lks = [str(lk.id) for lk in old_user.label_keybinds]

    async with TaskService.new(sessionmaker()) as tasks_service:
        old_task = await tasks_service.get_one(id=test_task["id"])
        old_task_lks = [str(lk.id) for lk in old_task.label_keybinds]

    response = await client.delete(urls.UNASSIGN_TASK, params={"task_id": test_task["id"]})

    async with UserService.new(sessionmaker()) as users_service:
        user = await users_service.get_one(id=test_user["id"])  # type: ignore
        user_lks = [str(lk.id) for lk in user.label_keybinds]

    async with TaskService.new(sessionmaker()) as tasks_service:
        task = await tasks_service.get_one(id=test_task["id"])
        task_lks = [str(lk.id) for lk in task.label_keybinds]

    assert test_task["id"] not in [t.id for t in user.assigned_tasks]
    assert old_user_lks == user_lks
    assert old_task_lks == task_lks
    assert response.status_code == HTTP_200_OK

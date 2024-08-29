import json
import random
from typing import Any, cast
from uuid import UUID

import pytest
from fixture_options import FIXTURE_OPTIONS, TestTask
from litestar import Litestar
from litestar.response import File
from litestar.testing import AsyncTestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain import urls
from app.domain.schema import Annotation, Task

pytestmark = pytest.mark.anyio

with open("tests/fixtures/tasks.json") as jf:
    tmp = json.load(jf)
    test_task: dict[str, str] = tmp[0]
    random_task: dict[str, str] = tmp[1]


class TestAnnotations:
    @pytest.fixture(name="test_annotation")
    async def annotation_fixture(self, test_task: TestTask, session: AsyncSession) -> Annotation:
        task = (
            await session.execute(select(Task).where(Task.id == UUID(test_task["id"])))
        ).scalar_one()
        annotation = task.annotations[0]

        return annotation

    @pytest.mark.parametrize(
        "annotation_id, expected_status, expected_json",
        [
            (
                999,
                403,
                {"detail": "Annotation does not belong to task!"},
            ),
            (1, 200, None),
        ],
        ids=["sad_annotation-not-in-task", "happy"],
    )
    async def test_get_annotation(  # noqa: PLR0913 (too many arguments)
        self,
        client: AsyncTestClient[Litestar],
        test_task: TestTask,
        annotation_id: int,
        expected_status: int,
        expected_json: dict[Any, Any] | None,
    ) -> None:
        response = await client.get(
            urls.GET_ANY_ANNOTATION,
            params={"task_id": test_task["id"], "annotation_id": annotation_id},
        )
        assert response.status_code == expected_status
        if expected_json is not None:
            assert (
                expected_json.items() <= response.json().items()
            )  # is expected_json subset of response.json


async def test_get_next_annotation_none_left(
    client: AsyncTestClient[Litestar], session: AsyncSession, test_task: TestTask
) -> None:
    """Test response to get next annotation for task when there are no more annotations to label"""
    async with session.begin():
        task = (await session.execute(select(Task).where(Task.id == test_task["id"]))).scalar_one()
        for anno in task.annotations:
            anno.labeled = True
            anno.label = random.choice(["humerus", "scapula", "tibia", "meniscus"])

    response = await client.get(urls.GET_NEXT_ANNOTATION, params={"task_id": test_task["id"]})
    assert response.headers["X-Metadata-AnnotationID"] == "-999"


async def test_get_next_annotation_happy(
    client: AsyncTestClient[Litestar], test_task: TestTask
) -> None:
    response = await client.get(urls.GET_NEXT_ANNOTATION, params={"task_id": test_task["id"]})
    file_response = cast(File, response)
    assert file_response.headers.get("X-Metadata-AnnotationID") is not None
    assert "image" in file_response.headers.get("content-type", "")


@pytest.mark.parametrize(
    "task_id, annotation_id, expected_status, expected_response",
    [
        (random_task["id"], 1, 403, {"detail": "Task does not belong to user!"}),
        (
            test_task["id"],
            1,
            200,
            {
                "total": FIXTURE_OPTIONS.num_annotations_per_task,
                "labeled": 1,
                "progress": (1 / FIXTURE_OPTIONS.num_annotations_per_task) * 100,
            },
        ),
    ],
    ids=["sad_task-not-assigned-user", "happy"],
)
async def test_update_annotation(
    client: AsyncTestClient[Litestar],
    task_id: str,
    annotation_id: int,
    expected_status: int,
    expected_response: dict[Any, Any],
) -> None:
    # Sad Path: User updating task that does not belong to him results in PermissionDeniedException
    # Happy Path: User updating task returns dictionary with updated progress values -- check values for accuracy
    response = await client.patch(
        urls.UPDATE_ANNOTATION,
        params={"task_id": task_id, "annotation_id": annotation_id},
        json={"label": "humerus"},
    )
    assert response.status_code == expected_status
    assert expected_response.items() <= response.json().items()

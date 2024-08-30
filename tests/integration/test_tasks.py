import random
from pathlib import Path
from typing import Any, TypedDict
from urllib.parse import quote

import pytest
from app.domain import urls
from app.domain.schema import Annotation, Task
from fixture_options import TestTask
from litestar import Litestar
from litestar.status_codes import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
)
from litestar.testing import AsyncTestClient
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.anyio


class TestTaskCreation:
    @pytest.fixture(autouse=True)
    def setup(self, client: AsyncTestClient[Litestar]) -> None:
        """Necessary to guarantee that the instance attributes are set before any test runs"""
        self.client = client
        self.test_task = {
            "title": "Another Test Task",  # test will break if this matches any fixture task title
            "root": quote(
                "/home/sameed/projects/hfhs_annotation_interface/tests/fixtures/annotations/test"
            ),
            "label_keybinds": [
                {"label": "bicep", "keybind": "a"},
                {"label": "humerus", "keybind": "s"},
                {"label": "tibia", "keybind": "d"},
                {"label": "femur", "keybind": "f"},
            ],
        }

    async def test_success(self):
        response = await self.client.post(
            urls.CREATE_TASK,
            json=self.test_task,
        )
        assert response.status_code == HTTP_201_CREATED

    async def test_unauthenticated_user(self):
        """
        TODO: this test currently fails because setting session data doesn't remove
        previously defined other active user from session
        """
        await self.client.set_session_data({"user_id": None})  # remove active user from session
        response = await self.client.post(urls.CREATE_TASK, json=self.test_task)
        assert response.status_code == HTTP_401_UNAUTHORIZED

    async def test_label_keybind_creation(
        self, test_user: dict[str, str | int | float], session: AsyncSession
    ):
        """When a task is created, corresponding default label keybinds should be generated"""
        await self.client.post(
            urls.CREATE_TASK,
            json=self.test_task,
        )
        inserted_task = (
            await session.execute(select(Task).where(Task.title == self.test_task["title"]))
        ).scalar_one()
        inserted_lks = [
            {"label": lk.to_dict()["label"], "keybind": lk.to_dict()["keybind"]}
            for lk in inserted_task.label_keybinds
        ]
        assert inserted_lks == self.test_task["label_keybinds"]

    async def test_annotation_creation(self, session: AsyncSession):
        """When a task is created, corresponding annotations should be created for images in root"""
        await self.client.post(
            urls.CREATE_TASK,
            json=self.test_task,
        )
        inserted_task = (
            await session.execute(select(Task).where(Task.title == self.test_task["title"]))
        ).scalar_one()

        inserted_annos = [anno.to_dict() for anno in inserted_task.annotations]

        for anno in inserted_annos:
            fp_anno = Path(anno["filepath"])
            fp_task = Path(inserted_task.root_folder)

            assert fp_anno.exists(), fp_anno
            assert fp_anno.is_relative_to(fp_task), f"task: {fp_task}; annotation: {fp_anno}"
            assert anno["label"] is None
            assert not anno["labeled"]

    testdata = [
        [
            ("a" * 51),  # title too long
            "/home/sameed/projects/hfhs_annotation_interface/tests/fixtures/annotations/test",
            ["testlabel"],
            ["a"],
            "at most 50",
        ],
        [
            "some_title",
            "/home/nonexistent",  # path does not exist
            ["testlabel"],
            ["a"],
            "does not exist",
        ],
        [
            "some_title",
            "/home/sameed/projects/hfhs_annotation_interface/tests/integration/test_tasks.py",
            ["testlabel"],
            ["a"],
            "not a directory",
        ],
        [
            "some_title",
            "/home/sameed/projects/hfhs_annotation_interface/tests/fixtures/annotations/test",
            [("f" * 21)],  # label too long
            ["a"],
            "at most 20",
        ],
        [
            "some_title",
            "/home/sameed/projects/hfhs_annotation_interface/tests/fixtures/annotations/test",
            ["testlabel"],
            ["ab"],  # keybind too long
            "at most 1",
        ],
        [
            "some_title",
            "/home/sameed/projects/hfhs_annotation_interface/tests/fixtures/annotations/test",
            ["testlabel"],
            ["z"],  # illegal keybind (reserved for ctrl+z)
            "is reserved",
        ],
        [
            "some_title",
            "/home/sameed/projects/hfhs_annotation_interface/tests/fixtures/annotations/test",
            ["testlabel", "testlabel"],  # duplicate label
            ["a", "s"],
            "Duplicate label",
        ],
        [
            "some_title",
            "/home/sameed/projects/hfhs_annotation_interface/tests/fixtures/annotations/test",
            ["testlabel", "another"],
            ["a", "a"],  # duplicate keybind
            "Duplicate keybind",
        ],
    ]

    @pytest.mark.parametrize("title,root,labels,keybinds,error_msg", testdata)
    async def test_validations(
        self,
        title: str,
        root: str,
        labels: list[str],
        keybinds: list[str],
        error_msg: str,
    ):
        """Test whether validations for task data entry work"""
        task_construct = {
            "title": title,
            "root": quote(root),
            "label_keybinds": [{"label": j, "keybind": k} for (j, k) in zip(labels, keybinds, strict=False)],
        }

        response = await self.client.post(
            urls.CREATE_TASK,
            json=task_construct,
        )
        jsonified: dict[str, Any] = (
            response.json()
        )  # {... rest of the Response ..., 'extra': [{'key': ..., 'message': ...}]}
        assert jsonified["status_code"] == HTTP_400_BAD_REQUEST, jsonified
        assert error_msg in jsonified["extra"][0]["message"], jsonified


class TestTaskUpdate:
    """
    Test task update similar to form on task update page
    - Validations already tested in TestTaskCreation
    """

    @pytest.fixture(autouse=True)
    def setup(self, client: AsyncTestClient[Litestar]) -> None:
        self.client = client
        test_lks = [
            {"label": "humerus", "keybind": "q"},
            {"label": "hobie", "keybind": "u"},
            {"label": "gaga", "keybind": "w"},
            {"label": "homini", "keybind": "k"},
        ]
        tmp = [
            f
            for f in Path(
                "/home/sameed/projects/hfhs_annotation_interface/tests/fixtures/annotations"
            ).iterdir()
            if "test" in str(f)
        ][0]
        ttmp = list(tmp.iterdir())
        k = random.randint(1, len(ttmp))
        filenames = [str(fp) for fp in random.sample(ttmp, k)]

        class TempTypeDict(TypedDict):
            label_keybinds: list[dict[str, str]]
            files: list[str]

        self.task: TempTypeDict = {"label_keybinds": test_lks, "files": filenames}

    async def test_success(
        self,
        client: AsyncTestClient[Litestar],
        test_task: TestTask,
        session: AsyncSession,
    ):
        """Happy path for update"""
        response = await client.patch(
            urls.UPDATE_TASK, json=self.task, params={"task_id": test_task["id"]}
        )
        updated_task = (
            await session.execute(select(Task).where(Task.id == test_task["id"]))
        ).scalar_one()
        updated_lks = [
            {"label": lk.label, "keybind": lk.keybind} for lk in updated_task.label_keybinds
        ]
        updated_annos = [anno.to_dict() for anno in updated_task.annotations]
        updated_filepaths = [anno["filepath"] for anno in updated_annos]

        assert all([lk in updated_lks for lk in self.task["label_keybinds"]])
        assert sorted(self.task["files"]) == sorted(updated_filepaths)
        assert response.status_code == HTTP_200_OK

    async def test_success_partial_filepaths(
        self,
        client: AsyncTestClient[Litestar],
        test_task: TestTask,
        session: AsyncSession,
    ):
        # label some annotations
        stmt = (
            update(Annotation)
            .where(Annotation.task_id == test_task["id"])
            .values(label="pancreas", labeled=True)
        )
        await session.execute(stmt)
        await session.commit()

        old_task = (
            await session.execute(select(Task).where(Task.id == test_task["id"]))
        ).scalar_one()
        old_annos = [anno.to_dict() for anno in old_task.annotations]
        old_filepaths = [anno["filepath"] for anno in old_annos]
        new_test_task = self.task
        new_test_task["files"].extend(old_filepaths)

        response = await client.patch(
            urls.UPDATE_TASK, json=new_test_task, params={"task_id": test_task["id"]}
        )

        await session.refresh(old_task)
        updated_lks = [{"label": lk.label, "keybind": lk.keybind} for lk in old_task.label_keybinds]
        updated_annos = [anno.to_dict() for anno in old_task.annotations]
        updated_filepaths = [anno["filepath"] for anno in updated_annos]

        assert all(
            [lk in updated_lks for lk in self.task["label_keybinds"]]
        ), f"updated: {updated_lks}\nexpected: {new_test_task['label_keybinds']}"
        assert sorted(new_test_task["files"]) == sorted(updated_filepaths)
        for anno in updated_annos:  # check that old annotations are still labeled
            if anno["filepath"] not in old_filepaths:
                continue
            assert anno["label"] is not None
            assert anno["labeled"]

        assert response.status_code == HTTP_200_OK

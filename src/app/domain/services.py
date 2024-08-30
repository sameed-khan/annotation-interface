from collections.abc import Sequence
from typing import Any
from uuid import UUID

from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService
from litestar.exceptions import NotAuthorizedException
from litestar.status_codes import HTTP_401_UNAUTHORIZED
from sqlalchemy import select

from app.domain.repositories import (
    AnnotationRepository,
    LabelKeybindRepository,
    TaskRepository,
    UserRepository,
)
from app.domain.schema import Annotation, LabelKeybind, Task, User


class UserService(SQLAlchemyAsyncRepositoryService[User]):
    """Handles database operations for users."""

    repository_type = UserRepository

    def __init__(self, **repo_kwargs: Any) -> None:
        self.repository: UserRepository = self.repository_type(**repo_kwargs)  # type: ignore
        self.model_type = self.repository.model_type

    async def authenticate(self, request_username: str, request_password: str) -> User:
        # TODO: implement password hashing
        """Authenticate a user.

        Args:
            username (str): username
            password (str): password

        Raises:
            NotAuthorizedException: Raised when user does not exist or password is invalid.

        Returns:
            User: User object
        """

        db_obj = await self.get_one_or_none(
            username=request_username
        )  # NOTE: username = username (same arg name) causes auth failure

        if db_obj is None:
            msg = "User not found"
            raise NotAuthorizedException(msg, status_code=HTTP_401_UNAUTHORIZED)
        elif db_obj.password != request_password:
            msg = "Incorrect password"
            raise NotAuthorizedException(msg, status_code=HTTP_401_UNAUTHORIZED)

        return db_obj


class TaskService(SQLAlchemyAsyncRepositoryService[Task]):
    """Handles database operations for tasks."""

    repository_type = TaskRepository

    def __init__(self, **repo_kwargs: Any) -> None:
        self.repository: TaskRepository = self.repository_type(**repo_kwargs)  # type: ignore
        self.model_type = self.repository.model_type

    async def get_all_tasks(self) -> Sequence[Task]:
        """Get all tasks."""
        stmt = select(Task).order_by(Task.created_at).distinct()
        results = await self.repository.session.execute(stmt)
        return results.scalars().unique().all()

    async def get_many_by_id(self, identifiers: Sequence[str | int]) -> Sequence[Task]:
        stmt = select(Task).where(Task.id.in_(identifiers))
        results = await self.repository.session.execute(stmt)
        res = results.scalars().all()
        if len(res) > 0:
            return res

        return []

    async def update_task(
        self,
        task_id: UUID,
        user_id: UUID,
        label_keybinds: list[LabelKeybind],
        annotations: list[Annotation],
    ) -> Task:
        """Update a task with new label keybinds and annotations."""
        async with self.repository.session.begin():
            task = await self.get_one(id=task_id)
            await self._update_task_label_keybinds(user_id, task, label_keybinds)
            await self._update_task_annotations(task, annotations)

        return task

    async def _update_task_label_keybinds(
        self, user_id: UUID, task: Task, label_keybinds: list[LabelKeybind]
    ) -> Task:
        """Update a task's label keybinds."""
        # Remove all label keybinds for the user, preserving other users' keybinds
        task.label_keybinds = [lk for lk in task.label_keybinds if lk.user_id != user_id]
        task.label_keybinds.extend(label_keybinds)
        return task

    async def _update_task_annotations(self, task: Task, annotations: list[Annotation]) -> Task:
        """
        Update a task's annotations. Selectively replaces annotations
        Case 1: Previously selected, still selected annotation
        Case 2: Previously selected, now unselected annotation
        Case 3: Previously unselected, now selected annotation
        """
        task_annos_updated: list[Annotation] = []
        anno_filepaths = [anno.filepath for anno in annotations]
        idxs_to_remove: list[int] = []
        for anno in task.annotations:
            if anno.filepath in anno_filepaths:  # was previously selected, still selected
                task_annos_updated.append(anno)
                # the above annotation is the same as the one in the task so we do not have to
                # save it to later add to the task's annotations through list.extend and
                # cause the annotation label to be reset
                idxs_to_remove.append(anno_filepaths.index(anno.filepath))
            else:  # was previously selected, now unselected
                continue  # do not add to task_annos_updated

        # pop indices in descending order to prevent index out of range errors
        for idx in sorted(idxs_to_remove, reverse=True):
            annotations.pop(idx)

        task.annotations = task_annos_updated
        task.annotations.extend(annotations)  # now clear of duplicates, handles case 3
        return task


class LabelKeybindService(SQLAlchemyAsyncRepositoryService[LabelKeybind]):
    """Handles database operations for label keybinds."""

    repository_type = LabelKeybindRepository

    def __init__(self, **repo_kwargs: Any) -> None:
        self.repository: LabelKeybindRepository = self.repository_type(**repo_kwargs)  # type: ignore
        self.model_type = self.repository.model_type


class AnnotationService(SQLAlchemyAsyncRepositoryService[Annotation]):
    """Handles database operations for annotations."""

    repository_type = AnnotationRepository

    def __init__(self, **repo_kwargs: Any) -> None:
        self.repository: AnnotationRepository = self.repository_type(**repo_kwargs)  # type: ignore
        self.model_type = self.repository.model_type

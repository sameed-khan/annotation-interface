from typing import Any, Sequence

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

from typing import Any

from app.domain.schema import User, Task
from app.domain.repositories import UserRepository, TaskRepository

from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService

from litestar.exceptions import NotAuthorizedException
from litestar.status_codes import HTTP_401_UNAUTHORIZED

class UserService(SQLAlchemyAsyncRepositoryService[User]): 
    """Handles database operations for users."""

    repository_type = UserRepository

    def __init__(self, **repo_kwargs: Any) -> None:
        self.repository: UserRepository = self.repository_type(**repo_kwargs)  # type: ignore
        self.model_type = self.repository.model_type

    async def create(
        self,
        data,  # TODO: Type hint this properly - ModelDictT doesn't seem to be an importable thing from advanced_alchemy.service
        *,
        auto_commit: bool | None = None,
        auto_expunge: bool | None = None,
        auto_refresh: bool | None = None,
    ) -> User:
        """ Create a new User."""
        if isinstance(data, dict):
            data = await self.to_model(data, "create")

        return await super().create(
            data=data, 
            auto_commit=auto_commit,
            auto_expunge=auto_expunge, 
            auto_refresh=auto_refresh
        )

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

        db_obj = await self.get_one_or_none(username=request_username)  # NOTE: username = username (same arg name) causes auth failure

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
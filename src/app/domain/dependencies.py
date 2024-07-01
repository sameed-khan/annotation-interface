from typing import TYPE_CHECKING

from app.domain.services import UserService, TaskService
from app.domain.schema import User, Task

from sqlalchemy.orm import selectinload

# if TYPE_CHECKING:
from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

async def provide_users_service(db_session: AsyncSession) -> AsyncGenerator[UserService, None]:
    """Construct repository and service objects for the request."""
    async with UserService.new(
        session=db_session,
        load = [
            selectinload(User.created_tasks).options(selectinload(Task.creator)),
            selectinload(User.assigned_tasks),
            selectinload(User.label_keybinds),
        ]
    ) as service:
        yield service

async def provide_tasks_service(db_session: AsyncSession) -> AsyncGenerator[TaskService, None]:
    """Construct repository and service objects for the request."""
    async with TaskService.new(
        session=db_session,
        load = [
            selectinload(Task.creator),
            selectinload(Task.contributors),
            selectinload(Task.annotations),
            selectinload(Task.label_keybinds),
        ]
    ) as service:
        yield service
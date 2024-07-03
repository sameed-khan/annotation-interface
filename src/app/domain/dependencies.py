# if TYPE_CHECKING:
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.schema import Annotation, LabelKeybind, Task, User
from app.domain.services import AnnotationService, LabelKeybindService, TaskService, UserService


async def provide_users_service(db_session: AsyncSession) -> AsyncGenerator[UserService, None]:
    """Construct repository and service objects for the request."""
    async with UserService.new(
        session=db_session,
        load=[
            selectinload(User.created_tasks).options(selectinload(Task.creator)),
            selectinload(User.assigned_tasks),
            selectinload(User.label_keybinds),
        ],
    ) as service:
        yield service


async def provide_tasks_service(db_session: AsyncSession) -> AsyncGenerator[TaskService, None]:
    """Construct repository and service objects for the request."""
    async with TaskService.new(
        session=db_session,
        load=[
            selectinload(Task.creator),
            selectinload(Task.contributors),
            selectinload(Task.annotations),
            selectinload(Task.label_keybinds),
        ],
    ) as service:
        yield service


async def provide_label_keybinds_service(
    db_session: AsyncSession,
) -> AsyncGenerator[LabelKeybindService, None]:
    """Construct repository and service objects for the request."""
    async with LabelKeybindService.new(
        session=db_session,
        load=[
            selectinload(LabelKeybind.user),
            selectinload(LabelKeybind.task),
        ],
    ) as service:
        yield service


async def provide_annotations_service(
    db_session: AsyncSession,
) -> AsyncGenerator[AnnotationService, None]:
    """Construct repository and service objects for the request."""
    async with AnnotationService.new(
        session=db_session,
        load=[
            selectinload(Annotation.associated_task),
        ],
    ) as service:
        yield service

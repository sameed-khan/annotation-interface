from advanced_alchemy.repository import SQLAlchemyAsyncRepository

from app.domain.schema import Annotation, LabelKeybind, Task, User


class UserRepository(SQLAlchemyAsyncRepository[User]):
    """User SQLAlchemy Repository."""

    model_type = User


class TaskRepository(SQLAlchemyAsyncRepository[Task]):
    """Task SQLAlchemy Repository."""

    model_type = Task


class LabelKeybindRepository(SQLAlchemyAsyncRepository[LabelKeybind]):
    """LabelKeybind SQLAlchemy Repository."""

    model_type = LabelKeybind


class AnnotationRepository(SQLAlchemyAsyncRepository[Annotation]):
    """Annotation SQLAlchemy Repository."""

    model_type = Annotation

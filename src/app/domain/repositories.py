from advanced_alchemy.repository import SQLAlchemyAsyncRepository

from app.domain.schema import User, Task

class UserRepository(SQLAlchemyAsyncRepository[User]):
    """ User SQLAlchemy Repository."""
    model_type = User

class TaskRepository(SQLAlchemyAsyncRepository[Task]):
    """ Task SQLAlchemy Repository."""
    model_type = Task
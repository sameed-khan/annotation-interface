from os import urandom
from typing import Any, Dict

from advanced_alchemy.base import orm_registry

# from advanced_alchemy.config import EngineConfig
from advanced_alchemy.config.asyncio import AsyncSessionConfig
from advanced_alchemy.extensions.litestar.plugins.init.config.asyncio import (
    autocommit_before_send_handler,
)
from jinja2 import Environment, FileSystemLoader
from litestar import Litestar
from litestar.connection import ASGIConnection
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.contrib.sqlalchemy.plugins import SQLAlchemyAsyncConfig, SQLAlchemyPlugin
from litestar.middleware.session.client_side import ClientSideSessionBackend, CookieBackendConfig
from litestar.security.session_auth import SessionAuth
from litestar.static_files import create_static_files_router
from litestar.template.config import TemplateConfig
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.domain import urls
from app.domain.controllers import PageController, SystemController, TaskController, UserController
from app.domain.schema import User
from app.domain.template_filters import format_and_localize_timestamp, reduce_slashes

# class Base(DeclarativeBase):
#     pass

# user_tasks = Table("user_tasks", Base.metadata,
#     Column("user_id", ForeignKey("users.uuid"), primary_key=True),
#     Column("task_id", ForeignKey("tasks.uuid"), primary_key=True)
# )

# class User(Base):
#     __tablename__ = "users"
#     __table_args__ = {"extend_existing": True}
#     uuid: Mapped[UUID] = mapped_column(Text, primary_key=True, default=uuid4)
#     username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
#     password: Mapped[str] = mapped_column(String, nullable=False)
#     date_created: Mapped[date] = mapped_column(DateTime, default=func.now(), nullable=False)
#     annotation_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

#     created_tasks = relationship("Task", back_populates="creator", lazy="selectin")
#     contributed_tasks = relationship("Task", secondary=user_tasks, back_populates="contributors", lazy="selectin")
#     label_keybinds = relationship("LabelKeybind", back_populates="user", lazy="selectin", cascade="all, delete")

# class Task(Base):
#     __tablename__ = "tasks"
#     __table_args__ = {"extend_existing": True}
#     uuid: Mapped[UUID] = mapped_column(Text, primary_key=True, default=uuid4)
#     title: Mapped[str] = mapped_column(String, nullable=False)
#     root_folder: Mapped[str] = mapped_column(String, nullable=False)
#     creator_id: Mapped[UUID] = mapped_column(Text, ForeignKey("users.uuid"))
#     last_updated: Mapped[date] = mapped_column(DateTime, default=func.now(), nullable=False)

#     creator = relationship("User", back_populates="created_tasks", lazy="selectin")
#     contributors = relationship("User", secondary=user_tasks, back_populates="contributed_tasks", lazy="selectin", cascade="all, delete")
#     annotations = relationship("Annotation", back_populates="associated_task", lazy="selectin", cascade="all, delete")
#     label_keybinds = relationship("LabelKeybind", back_populates="task", lazy="selectin", cascade="all, delete")

# class Annotation(Base):
#     __tablename__ = "annotations"
#     __table_args__ = {"extend_existing": True}
#     id: Mapped[int] = mapped_column(Integer, primary_key=True)
#     label: Mapped[Optional[str]] = mapped_column(String, nullable=True)
#     labeled: Mapped[bool] = mapped_column(Boolean, nullable=False)
#     created_time: Mapped[date] = mapped_column(DateTime, default=func.now(), nullable=False)
#     labeled_time: Mapped[Optional[date]] = mapped_column(DateTime, nullable=True)
#     labeled_by: Mapped[Optional[str]] = mapped_column(String, nullable=True)
#     filepath: Mapped[str] = mapped_column(String, nullable=False)
#     task_id: Mapped[UUID] = mapped_column(Text, ForeignKey("tasks.uuid"))

#     associated_task = relationship("Task", back_populates="annotations", lazy="selectin")

# class LabelKeybind(Base):
#     __tablename__ = "label_keybinds"
#     __table_args__ = {"extend_existing": True}
#     uuid: Mapped[UUID] = mapped_column(Text, primary_key=True, default=uuid4)
#     label: Mapped[str] = mapped_column(String, nullable=False)
#     keybind: Mapped[str] = mapped_column(String, nullable=False)
#     user_id: Mapped[UUID] = mapped_column(Text, ForeignKey("users.uuid"))
#     task_id: Mapped[UUID] = mapped_column(Text, ForeignKey("tasks.uuid"))

#     user = relationship("User", back_populates="label_keybinds", lazy="selectin")
#     task = relationship("Task", back_populates="label_keybinds", lazy="selectin")


# async def provide_transaction(db_session: AsyncSession) -> AsyncGenerator[AsyncSession, None]:
#     try:
#         async with db_session.begin():
#             yield db_session
#     except IntegrityError as exc:
#         raise ClientException(
#             status_code=HTTP_409_CONFLICT,
#             detail=str(exc)
#         ) from exc

# async def get_user_by_username(username: str, db_session: AsyncSession) -> User:
#     query = select(User).where(User.username == username)
#     result = await db_session.execute(query)
#     user = result.scalars().first()
#     if user is None:
#         raise NotFoundException(detail="User not found")
#     return user

# async def get_user_by_id(user_uuid: str | UUID, db_session: AsyncSession) -> User:
#     query = select(User).where(User.uuid == user_uuid)
#     result = await db_session.execute(query)
#     user = result.scalars().first()
#     if user is None:
#         raise NotFoundException(detail="User not found")
#     return user

# async def add_new_user(new_username: str, new_password: str, db_session: AsyncSession) -> User:
#     user = User(
#         uuid = str(uuid4()),
#         username = new_username,
#         password = new_password,
#         date_created = datetime.now(),
#         annotation_rate = 0.0
#     )
#     db_session.add(user)
#     return user

# async def get_tasks_for_user_id(user_uuid: str | UUID, db_session: AsyncSession) -> list[Task]:
#     user = await get_user_by_id(user_uuid, db_session)
#     return user.contributed_tasks

# async def get_binds_for_user_and_task(user_uuid: str | UUID, task_uuid: str | UUID, db_session: AsyncSession) -> Sequence[LabelKeybind]:
#     query = (
#         select(LabelKeybind)
#         .where(
#             and_(
#                 LabelKeybind.user_id == user_uuid,
#                 LabelKeybind.task_id == task_uuid
#             )
#         )
#     )
#     result = await db_session.execute(query)
#     binds = result.scalars().all()
#     if not binds:
#         raise NotFoundException(detail=f"No keybinds found for user {user_uuid} and task {task_uuid}")
#     return binds

# async def get_progress_information(task_id: str, db_session: AsyncSession) -> Tuple[int, int, int]:
#     labeled_count_query = ( select(func.count(Annotation.id))
#                            .where(
#                                and_(
#                                       Annotation.task_id == task_id,
#                                       Annotation.labeled == True
#                                 )
#                            ))
#     total_count_query = (select(func.count(Annotation.id)).where(Annotation.task_id == task_id))
#     r1, r2 = await db_session.execute(labeled_count_query), await db_session.execute(total_count_query)
#     labeled_count, total_count = r1.scalar_one(), r2.scalar_one()

#     return labeled_count, total_count, round((labeled_count / total_count) * 100)

# @dataclass
# class UserData:
#     username: str
#     password: str

# @dataclass
# class AnnotationUpdate:
#     task_uuid: str
#     annotation_id: int
#     label: str

# @get(path="/", status_code=HTTP_302_FOUND)
# async def login_redirect() -> Redirect:
#     # TODO: Check if user has valid cookie before redirecting
#     return Redirect(path="/login")

# @get(path="/login")
# async def login_page() -> Template:
#     return Template(template_name="login.html.jinja2", context={})

# @post(path="/login")
# async def login(
#     data: Annotated[UserData, Body(media_type=RequestEncodingType.URL_ENCODED)],
#     transaction: AsyncSession,
#     request: Request[Any, Any, Any]
# ) -> Response:
#     try:
#         user = await get_user_by_username(data.username, transaction)
#     except NotFoundException:
#         return Response(status_code=HTTP_401_UNAUTHORIZED, content="User not found")

#     if user.password != data.password:
#         return Response(status_code=HTTP_401_UNAUTHORIZED, content="Invalid password")

#     request.set_session({"user_id": str(user.uuid)})  # Store UUID as string
#     return Redirect(path="/panel")

# @get(path="/login/check_user")
# async def check_username(username_to_check: str, transaction: AsyncSession) -> Response:
#     try:
#         await get_user_by_username(username_to_check, transaction)
#         return Response({"username_in_use": True}, status_code=HTTP_409_CONFLICT)
#     except NotFoundException:
#         return Response({"username_in_use": False}, status_code=HTTP_200_OK)


# @post(path="/login/new_user")
# async def create_new_user(
#     data: Annotated[UserData, Body(media_type=RequestEncodingType.URL_ENCODED)],
#     transaction: AsyncSession,
#     request: Request[Any, Any, Any]
# ) -> Response:
#     try:
#         user = await add_new_user(data.username, data.password, transaction)
#         request.set_session({"user_id": str(user.uuid)})  # Store UUID as string
#         return Redirect(path="/panel")
#     except IntegrityError:
#         # Handle the case where the username already exists
#         return Response(status_code=HTTP_409_CONFLICT, content="Username already exists")

# @get(path="/panel")
# async def panel_page(request: Request[User, Any, Any], transaction: AsyncSession) -> Template:
#     user_id_str: str = str(request.session.get("user_id"))

#     try:
#         user_tasks: list[Task] = await get_tasks_for_user_id(user_id_str, transaction)
#         user_as_dict_tasks: list[Dict[str, Any]] = []

#         for task in user_tasks:
#             task_annotations = task.annotations
#             labeled_count = len([a for a in task_annotations if a.labeled])
#             total_count = len(task_annotations)
#             task_creator_name = ( await get_user_by_id(task.creator_id, transaction) ).username

#             task_dict = {
#                 "labeled_count": labeled_count,
#                 "total_count": total_count,
#                 "creator_name": task_creator_name,
#                 **task.__dict__
#             }
#             user_as_dict_tasks.append(task_dict)

#         # task_binds = list[LabelKeybind] = await
#         return Template(template_name="panel.html.jinja2", context={"task_list": user_as_dict_tasks})

#     except ValueError:
#         raise NotAuthorizedException("Invalid user ID in session")

# @get(path="/panel/get_task_keybinds")
# async def get_task_keybinds(task_id: str, request: Request[Any, Any, Any], transaction: AsyncSession) -> Response:
#     user_id = request.session.get("user_id")
#     result = await transaction.execute(select(Task).where(Task.uuid == task_id))
#     task = result.scalars().first()

#     if user_id is None:
#         return Response(status_code=HTTP_401_UNAUTHORIZED, content="User not found")
#     elif task is None:
#         return Response(status_code=HTTP_404_NOT_FOUND, content="Task not found")

#     label_keybinds = await get_binds_for_user_and_task(user_id, task_id, transaction)

#     return Response({
#         "label_keybinds": [{ "label": bind.label, "keybind": bind.keybind } for bind in label_keybinds],
#         "files": [{ "included": True, "name": nm } for nm in os.listdir(task.root_folder)]  # TODO: Filter out non-image files
#     }, status_code=HTTP_200_OK)


# @get(path="/panel/get_task_profile_picture", media_type="image/*")
# async def get_task_profile_picture(root_folder: str) -> File | None:
#     extensions_dict = {
#         "jpg": "image/jpeg",
#         "jpeg": "image/jpeg",
#         "png": "image/png",
#         "gif": "image/gif",
#         "bmp": "image/bmp",
#         "webp": "image/webp",
#         "svg": "image/svg+xml",
#         "tif": "image/tiff",
#         "tiff": "image/tiff",

#     }
#     root = Path(root_folder)
#     for file in root.iterdir():
#         if file.suffix.lower().lstrip(".") in extensions_dict:
#             return File(
#                 file.resolve(),
#                 media_type=extensions_dict[file.suffix.lower().lstrip(".")],
#             )

# @get(path="/label")
# async def label_page(task_id: str, transaction: AsyncSession, request: Request[Any, Any, Any]) -> Template:
#     labeled_count, total_count, progress_percent = await get_progress_information(task_id, transaction)

#     user_id: str | None = request.session.get("user_id")
#     if user_id is None:
#         raise NotAuthorizedException("User not found in session")

#     lks = await get_binds_for_user_and_task(user_id, task_id, transaction)
#     label_keybinds = [{ "label": lk.label, "keybind": lk.keybind } for lk in lks]

#     return Template(template_name="label.html.jinja2", context={
#         "task_uuid": task_id,
#         "labeled": labeled_count,
#         "total": total_count,
#         "progress_percent": progress_percent,
#         "label_keybinds": label_keybinds
#     })

# @get(path="/label/get_next_annotation")
# async def label_get_next_image(task_uuid: str, transaction: AsyncSession) -> Response:
#     query = select(Annotation).where(Annotation.task_id == task_uuid, Annotation.labeled == False).limit(1)
#     result = await transaction.execute(query)
#     anno = result.scalars().one_or_none()

#     anno_id = anno.id if anno is not None else 0
#     return Response({"next_id": anno_id}, status_code=HTTP_200_OK)

# @get(path="/label/get_image")  # TODO: handle converting DICOM to PNG and other image types
# async def label_get_image(annotation_id: str, transaction: AsyncSession) -> Response:
#     if annotation_id == 0 or annotation_id is None or annotation_id == "0" or annotation_id == "null":
#         file_path = os.path.join(os.getcwd(), "static/assets/task-completed.png")
#         return File(file_path, media_type="image/png")

#     query = select(Annotation).where(Annotation.id == annotation_id)
#     result = await transaction.execute(query)
#     anno = result.scalars().one()

#     return File(anno.filepath, media_type="image/png")

# @patch(path="/label/update_annotation")
# async def label_update_annotation(data: AnnotationUpdate, transaction: AsyncSession, request: Request[Any, Any, Any]) -> Response:
#     if data.annotation_id < 1:
#         labeled_count, total_count, progress_percent = await get_progress_information(data.task_uuid, transaction)
#         return Response({
#             "next_id": 0,
#             "labeled": labeled_count,
#             "total": total_count,
#             "progress_percent": progress_percent
#         }, status_code=HTTP_202_ACCEPTED)

#     query = (select(User).where(User.uuid == request.session.get("user_id")))
#     result = await transaction.execute(query)
#     user = result.scalars().one()
#     username = user.username

#     stmt = (update(Annotation)
#         .where(Annotation.id == data.annotation_id)
#         .values(label=data.label, labeled=True, labeled_time=datetime.now(), labeled_by=username)
#     )
#     result = await transaction.execute(stmt)

#     query = (select(Annotation).where(Annotation.task_id == data.task_uuid, Annotation.labeled == False).limit(1))
#     result = await transaction.execute(query)
#     annotation = result.scalars().one_or_none()
#     next_id = annotation.id if annotation is not None else 0

#     labeled_count, total_count, progress_percent = await get_progress_information(data.task_uuid, transaction)

#     return Response({
#         "next_id": next_id,
#         "labeled": labeled_count,
#         "total": total_count,
#         "progress_percent": progress_percent
#     }, status_code=HTTP_200_OK)


# @patch(path="/label/undo_annotation")
# async def label_undo_annotation(data: AnnotationUpdate, transaction: AsyncSession) -> Response:
#     stmt = (update(Annotation)
#         .where(Annotation.id == data.annotation_id)
#         .values(label=None, labeled=False, labeled_time=None, labeled_by=None)
#     )
#     await transaction.execute(stmt)
#     labeled_count, total_count, progress_percent = await get_progress_information(data.task_uuid, transaction)
#     return Response({
#         "next_id": None,
#         "labeled": labeled_count,
#         "total": total_count,
#         "progress_percent": progress_percent
#     }, status_code=HTTP_200_OK)

# class User(UUIDAuditBase):
#     __tablename__ = "users"
#     __table_args__ = {"comment": "User accounts"}
#     username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
#     password: Mapped[str] = mapped_column(String, nullable=False)
#     annotation_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

# print(UUIDBase.metadata)

db_config = SQLAlchemyAsyncConfig(
    connection_string="sqlite+aiosqlite:///dev.db",
    metadata=orm_registry.metadata,
    create_all=True,
    before_send_handler=autocommit_before_send_handler,
    session_config=AsyncSessionConfig(expire_on_commit=True),
    # engine_config=EngineConfig(echo=True),  # type: ignore
)


async def retrieve_user_handler(
    session: Dict[str, Any], connection: ASGIConnection[Any, Any, Any, Any]
) -> User | None:
    user_id = session.get("user_id")
    if not user_id:
        return None

    engine = connection.app.state.get("engine")
    if engine is None:
        engine = create_async_engine("sqlite+aiosqlite:///dev.db")
        connection.app.state.engine = engine

    async with AsyncSession(engine) as db_session:
        query = select(User).where(User.id == user_id)
        result = await db_session.execute(query)
        return result.scalars().one_or_none()


session_auth = SessionAuth[User, ClientSideSessionBackend](
    retrieve_user_handler=retrieve_user_handler,  # type: ignore
    session_backend_config=CookieBackendConfig(secret=urandom(16)),
    exclude=[
        urls.LOGIN_PAGE,
        urls.LOGIN_USER,
        urls.CHECK_USERNAME,
        urls.STATIC_FILE_ENDPOINT,
        urls.SCHEMA_ENDPOINT,
    ],
)

jinja_env = Environment(loader=FileSystemLoader("static/templates"))  # NOTE: cannot prefix "/"
jinja_env.filters.update(
    {
        "reduce_slashes": reduce_slashes,
        "filter_timestamp": format_and_localize_timestamp,
    }
)

# async def on_startup() -> None:
#     """Initializes the database."""
#     async with db_config.get_engine().begin() as conn:
#         await conn.run_sync(Base.metadata.create_all)

app = Litestar(
    # route_handlers=[PageController, UserController, panel_page, check_username, create_new_user,
    #                 get_task_profile_picture, get_task_keybinds, label_update_annotation,
    #                 label_undo_annotation, label_page, label_get_next_image, label_get_image,
    #                 create_static_files_router(path="static", directories=["static"])],
    route_handlers=[
        PageController,
        UserController,
        SystemController,
        TaskController,
        create_static_files_router(
            path=urls.STATIC_FILE_ENDPOINT, directories=["static"]
        ),  # TODO: change static to be some constant defined somehwere else in a config
    ],
    template_config=TemplateConfig(instance=JinjaTemplateEngine.from_environment(jinja_env)),
    # on_startup=[on_startup],
    # dependencies={"transaction": provide_transaction},
    plugins=[SQLAlchemyPlugin(db_config)],
    on_app_init=[session_auth.on_app_init],
    middleware=[session_auth.middleware],
)

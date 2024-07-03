import os
from typing import Annotated, Any, Dict

from litestar import Controller, Request, get, post
from litestar.di import Provide
from litestar.enums import RequestEncodingType
from litestar.exceptions import NotFoundException
from litestar.params import Body
from litestar.response import Redirect, Response, Template
from litestar.status_codes import HTTP_200_OK, HTTP_201_CREATED, HTTP_404_NOT_FOUND

from app.domain import constants, urls
from app.domain.dependencies import (
    provide_annotations_service,
    provide_label_keybinds_service,
    provide_tasks_service,
    provide_users_service,
)
from app.domain.models import TaskData, UserData
from app.domain.schema import Annotation, LabelKeybind, Task, User
from app.domain.services import AnnotationService, LabelKeybindService, TaskService, UserService


class PageController(Controller):
    """Controller for serving pages to users."""

    dependencies = {"users_service": Provide(provide_users_service)}

    @get(
        path="/",
        operation_id="getIndexPage",
        name="frontend:index",
        exclude_from_auth=True,
        status_code=HTTP_200_OK,
    )
    async def index(self, request: Request[Any, Any, Any]) -> Redirect:
        """Serve page based on user login status."""
        if request.session.get("user_id") is not None:
            return Redirect(path=urls.TASK_PANEL_PAGE)

        return Redirect(path=urls.LOGIN_PAGE)

    @get(
        path=urls.LOGIN_PAGE,
        operation_id="getLoginPage",
        name="frontend:login_page",
        exclude_from_auth=True,
        status_code=HTTP_200_OK,
    )
    async def login_page(self) -> Template:
        """Serve login page"""
        return Template(
            template_name="login.html.jinja2",
            context={"login_user_route": urls.LOGIN_USER, "register_user_route": urls.CREATE_USER},
        )

    @get(
        path=urls.TASK_PANEL_PAGE,
        operation_id="getTaskPanelPage",
        name="frontend:panel_page",
        status_code=HTTP_200_OK,
    )
    async def panel_page(
        self, users_service: UserService, request: Request[User, Any, Any]
    ) -> Template:
        """Serve task management page."""

        user_id = request.session.get("user_id")
        user = await users_service.get(user_id)  # exception here means that authentication failed

        task_info_as_dicts = []
        for task in user.assigned_tasks:
            task_annotations = task.annotations
            creator_name = task.creator.username
            task_info_as_dicts.append(
                {
                    "labeled_count": len([a for a in task_annotations if a.labeled]),
                    "total_count": len(task_annotations),
                    "creator_name": creator_name,
                    "new_task_route": urls.CREATE_TASK,
                    **task.to_dict(),
                }
            )

        print(task_info_as_dicts)
        return Template(
            template_name="panel.html.jinja2", context={"task_list": task_info_as_dicts}
        )


class UserController(Controller):
    """Controller for user CRUD and authentication operations."""

    # TODO: get route for user?
    dependencies = {"users_service": Provide(provide_users_service)}

    @get(
        path=urls.CHECK_USERNAME,
        operation_id="checkUsername",
        name="user:check_username",
        exclude_from_auth=True,
        summary="Check if username is available",
        status_code=HTTP_200_OK,
    )
    async def check_username(
        self, users_service: UserService, request_username: str
    ) -> Response[Dict[str, bool]]:
        """Check if username is available."""
        user = await users_service.get_one_or_none(username=request_username)
        return Response(content={"available": user is None}, status_code=HTTP_200_OK)

    @post(
        path=urls.CREATE_USER,
        operation_id="createUser",
        name="user:create",
        exclude_from_auth=True,
        summary="Create new user",
        status_code=HTTP_201_CREATED,
    )
    async def create_user(
        self,
        users_service: UserService,
        data: Annotated[UserData, Body(media_type=RequestEncodingType.URL_ENCODED)],
        request: Request[Any, Any, Any],
    ) -> Redirect:
        """Create a new user."""
        user = await users_service.create(
            data=User(
                username=data.request_username,
                password=data.request_password,
            ),
            auto_commit=True,
            auto_expunge=True,
            auto_refresh=True,
        )
        print(f"Created user: {user.to_dict()}")
        request.set_session({"user_id": user.id})
        return Redirect(path=urls.TASK_PANEL_PAGE)

    @post(
        path=urls.LOGIN_USER,
        operation_id="loginUser",
        name="user:login",
        exclude_from_auth=True,
        summary="Login user",
        status_code=HTTP_200_OK,
    )
    async def login(
        self,
        users_service: UserService,
        data: Annotated[UserData, Body(media_type=RequestEncodingType.JSON)],
        request: Request[Any, Any, Any],
    ) -> Response[Dict[str, str]]:  # Add type parameters to Response
        # litestar automatically handles PermissionDeniedException and
        # transmission to client
        user = await users_service.authenticate(data.request_username, data.request_password)
        request.set_session({"user_id": user.id})
        return Response(
            content={"url": urls.TASK_PANEL_PAGE}, status_code=HTTP_200_OK
        )  # No Redirect since POST is coming from fetch


class TaskController(Controller):
    """Controller for task CRUD operations."""

    dependencies = {
        "tasks_service": Provide(provide_tasks_service),
        "annotations_service": Provide(provide_annotations_service),
        "label_keybinds_service": Provide(provide_label_keybinds_service),
    }

    @post(
        path=urls.CREATE_TASK,
        operation_id="createTask",
        name="task:create",
        exclude_from_auth=False,
        summary="Create new task",
        status_code=HTTP_201_CREATED,
    )
    async def create(  # noqa: PLR0913 (too many arguments)
        self,
        tasks_service: TaskService,
        annotations_service: AnnotationService,
        label_keybinds_service: LabelKeybindService,
        data: Annotated[TaskData, Body(media_type=RequestEncodingType.JSON)],
        request: Request[User, Any, Any],
    ) -> Response[Dict[str, str]]:
        """Create a new task."""
        creator_user_id = request.user.id
        new_task_id = (
            await tasks_service.create(
                data=Task(
                    title=data.title,
                    root_folder=data.root,
                    creator_id=creator_user_id,
                ),
                auto_commit=True,
                auto_expunge=True,
            )
        ).id  # NOTE: ORM objects' attributes cannot be referenced outside of method call
        # hence why the id is being 'statically' committed here
        await label_keybinds_service.create_many(
            data=[
                LabelKeybind(
                    label=lk["label"],
                    keybind=lk["keybind"],
                    user_id=creator_user_id,
                    task_id=new_task_id,
                )
                for lk in data.label_keybinds
            ],
            auto_commit=True,
            auto_expunge=False,
        )
        files_to_annotate = [
            os.path.abspath(fl)
            for fl in os.listdir(data.root)  # cannot use new_task.root_folder since not in ORM call
            if fl.endswith(tuple(constants.IMAGE_EXTENSIONS))
        ]
        new_annotations = await annotations_service.create_many(
            data=[
                Annotation(
                    label=None,
                    labeled=False,
                    labeled_by=None,
                    filepath=fl,
                    task_id=new_task_id,
                )
                for fl in files_to_annotate
            ],
            auto_commit=True,
            auto_expunge=False,
        )

        task_obj = await tasks_service.get_one(id=new_task_id)

        # Assign task to creator
        task_obj.contributors.append(task_obj.creator)  # can't use creator_user: already in session

        # Assign annotations to task
        task_obj.annotations.extend(new_annotations)

        # label keybinds backpopulates to user so no need to assign
        return Response(
            content={"message": "Task successfully created"}, status_code=HTTP_201_CREATED
        )


class SystemController(Controller):
    """Controller for exposing system information."""

    @get(
        path=urls.CHECK_PATH,
        operation_id="checkPath",
        name="system:check_path",
        exclude_from_auth=False,
        summary="Check if path is directory and get contents information",
        status_code=HTTP_200_OK,
    )
    async def check_path(self, path: str) -> Response[Dict[str, int]] | NotFoundException:
        """Check if path is directory and get contents information.
        Args:
            path (str): Path to check. Must be an absolute path and must exist on local filesystem.
        Returns:
            Response: Response listing number of files under directory, if it exists.
        """

        if not os.path.exists(path):
            msg = "Path does not exist"
            return NotFoundException(msg, status_code=HTTP_404_NOT_FOUND)

        elif not os.path.isdir(path):
            msg = "Path is not a directory"
            return NotFoundException(msg, status_code=HTTP_404_NOT_FOUND)

        valid_files = [
            fl
            for fl in os.listdir(path)
            if (
                fl.endswith(".png")
                or fl.endswith(".jpg")
                or fl.endswith(".jpeg")
                or fl.endswith(".bmp")
                or fl.endswith(".gif")
                or fl.endswith(".tiff")
                or fl.endswith(".dcm")
                or fl.endswith(".dicom")
            )
        ]
        return Response(content={"file_count": len(valid_files)}, status_code=HTTP_200_OK)

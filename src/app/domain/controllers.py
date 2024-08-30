import json
import os
from collections.abc import AsyncGenerator, Sequence
from pathlib import Path
from typing import Annotated, Any
from uuid import UUID

from litestar import Controller, MediaType, Request, delete, get, patch, post
from litestar.di import Provide
from litestar.enums import RequestEncodingType
from litestar.exceptions import NotFoundException, PermissionDeniedException
from litestar.params import Body
from litestar.response import File, Redirect, Response, Stream, Template
from litestar.status_codes import HTTP_200_OK, HTTP_201_CREATED

from app.domain import constants, urls
from app.domain.constants import KEYBOARD_LAYOUT
from app.domain.dependencies import (
    provide_annotations_service,
    provide_label_keybinds_service,
    provide_tasks_service,
    provide_users_service,
)
from app.domain.models import AnnotationUpdateData, TaskData, TaskUpdateData, UserData
from app.domain.schema import Annotation, LabelKeybind, Task, User
from app.domain.services import AnnotationService, LabelKeybindService, TaskService, UserService


class PageController(Controller):
    """Controller for serving pages to users."""

    dependencies = {
        "users_service": Provide(provide_users_service),
        "tasks_service": Provide(provide_tasks_service),
    }

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
    # TEMP: modify based on env
    async def login_page(self) -> Template:
        """Serve login page"""
        return Template(
            template_name="login/login.html.jinja2",
            context={"login_user_route": urls.LOGIN_USER, "register_user_route": urls.CREATE_USER},
        )

    @get(
        path=urls.TASK_PANEL_PAGE,
        operation_id="getTaskPanelPage",
        name="frontend:panel_page",
        status_code=HTTP_200_OK,
    )
    async def panel_page(
        self,
        tasks_service: TaskService,
        request: Request[User, Any, Any],
    ) -> Template:
        """Serve task management page."""

        user = request.user
        user_id = user.id
        # user_id = request.session.get("user_id")
        # user = await users_service.get(user_id)  # exception here means that authentication failed
        user_tasks: list[Task] = user.assigned_tasks

        # Populate assigned tasks list
        task_info_as_dicts: list[dict[str, Any]] = []
        for task in user_tasks:
            task_annotations = task.annotations
            selected_filepaths = [Path(a.filepath).resolve() for a in task_annotations]
            files_to_annotate = [
                {
                    "path": str(f),
                    "is_selected": Path(f).resolve() in selected_filepaths,
                }
                for f in list(Path(task.root_folder).iterdir())
                if f.suffix in constants.IMAGE_EXTENSIONS
            ]
            creator_name = task.creator.username if task.creator is not None else "Unknown"
            task_info_as_dicts.append(
                {
                    "labeled_count": len([a for a in task_annotations if a.labeled]),
                    "total_count": len(task_annotations),
                    "creator_name": creator_name,
                    "total": len(task_annotations),
                    "completed": len([a for a in task_annotations if a.labeled]),
                    "files": files_to_annotate,
                    **task.to_dict(),
                }
            )

        # Populate user's label keybinds for each assigned task
        label_keybinds_by_task: list[list[dict[str, str]]] = []
        for task in user_tasks:
            label_keybinds: list[LabelKeybind] = task.label_keybinds
            label_keybinds_by_task.append(
                [
                    {"label": lk.label, "keybind": lk.keybind, "id": str(lk.id)}
                    for lk in label_keybinds
                    if lk.user_id == user_id
                ]
            )

        # Populate global tasks list
        all_tasks: Sequence[Task] = await tasks_service.get_all_tasks()
        user_assigned_task_ids = [t.id for t in user.assigned_tasks]
        avail_tasks = [t for t in all_tasks if t.id not in user_assigned_task_ids]
        global_task_info_as_dicts: list[dict[str, str | int]] = []
        for task in avail_tasks:
            creator_name = task.creator.username if task.creator is not None else "Unknown"
            global_task_info_as_dicts.append(
                {
                    "labeled_count": len([a for a in task.annotations if a.labeled]),
                    "total_count": len(task.annotations),
                    "creator_name": creator_name,
                    "total": len(task.annotations),
                    "completed": len([a for a in task.annotations if a.labeled]),
                    **task.to_dict(),
                }
            )

        return Template(
            template_name="panel/panel.html.jinja2",
            context={
                "task_list": task_info_as_dicts,
                "global_task_list": global_task_info_as_dicts,
                "new_task_route": urls.CREATE_TASK,
                "existing_task_route": urls.ASSIGN_TASK,
                "task_label_keybinds": label_keybinds_by_task,
            },
        )

    @get(
        path=urls.LABEL_PAGE,
        operation_id="getLabelPage",
        name="frontend:label_page",
        status_code=HTTP_200_OK,
    )
    async def label_page(
        self,
        task_id: str,
        tasks_service: TaskService,
    ) -> Template:
        """Serve label page."""

        def sort_by_keyboard_layout(key: str):
            try:
                index = KEYBOARD_LAYOUT.index(key.lower())
            except ValueError:
                index = -1
            return index

        # TODO: add check to see if task id is within user_id?
        task = await tasks_service.get_one(id=task_id)
        lks = task.label_keybinds
        annotations = task.annotations
        labeled = len([a for a in annotations if a.labeled])
        total = len(annotations)

        label_keybinds = [{"label": lk.label, "keybind": lk.keybind} for lk in lks]
        label_keybinds.sort(key=lambda x: sort_by_keyboard_layout(x["keybind"]))
        context = {
            "labeled": labeled,
            "total": total,
            "progress_percent": round((labeled / total) * 100, 2),
            "label_keybinds": label_keybinds,
        }

        return Template(template_name="label/label.html.jinja2", context=context)

    @get(
        path=urls.TASK_THUMBNAIL,
        operation_id="getTaskThumbnail",
        name="frontend:task_thumbnail",
        status_code=HTTP_200_OK,
    )
    async def get_task_thumbnail(self, task_id: str, tasks_service: TaskService) -> File:
        task = await tasks_service.get_one(id=task_id)
        annotations = task.annotations
        path_to_first_image = annotations[0].filepath

        return File(path=Path(path_to_first_image).resolve(), media_type="image/png")


class UserController(Controller):
    """Controller for user CRUD and authentication operations."""

    # TODO: get route for user?
    dependencies = {
        "users_service": Provide(provide_users_service),
        "tasks_service": Provide(provide_tasks_service),
    }

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
    ) -> Response[dict[str, bool]]:
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
        data: Annotated[UserData, Body(media_type=RequestEncodingType.JSON)],
        request: Request[User, Any, Any],
    ) -> Response[dict[str, str]]:
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
        request.set_session({"user_id": user.id})  # type: ignore
        return Response(
            content={
                "id": str(user.id),
                "username": user.username,
                "url": urls.TASK_PANEL_PAGE,
            }
        )

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
    ) -> Response[dict[str, str]]:  # Add type parameters to Response
        # litestar automatically handles PermissionDeniedException and
        # transmission to client
        user = await users_service.authenticate(data.request_username, data.request_password)
        request.set_session({"user_id": user.id})  # type: ignore
        return Response(
            content={"url": urls.TASK_PANEL_PAGE}, status_code=HTTP_200_OK
        )  # No Redirect since POST is coming from fetch


class TaskController(Controller):
    """Controller for task CRUD operations."""

    dependencies = {
        "users_service": Provide(provide_users_service),
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
    ) -> Response[dict[str, str]]:
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
        root_folder = Path(data.root)
        files_to_annotate = [
            fl.resolve().as_posix()
            for fl in root_folder.iterdir()  # cannot use new_task.root_folder since not in ORM call
            if fl.suffix in constants.IMAGE_EXTENSIONS
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

    @post(
        path=urls.ASSIGN_TASK,
        operation_id="assignTask",
        name="task:assign_task",
        exclude_from_auth=False,
        summary="Assign task to current user",
        status_code=HTTP_200_OK,
    )
    async def assign_task(  # noqa: PLR0913 (too many arguments)
        self,
        users_service: UserService,
        tasks_service: TaskService,
        label_keybinds_service: LabelKeybindService,
        data: dict[str, list[str]],
        request: Request[User, Any, Any],
    ) -> Response[dict[str, str]]:
        """Assign task to current user."""

        user_id = request.user.id
        user = await users_service.get_one(id=user_id)
        tasks = await tasks_service.get_many_by_id(data["tasks_to_add_ids"])

        tasks_to_update: list[Task] = []
        new_lks: list[Sequence[LabelKeybind]] = []
        for task in tasks:
            # Skip creation of default keybinds for task if task already contains
            # any label keybinds previously assigned to user
            if any([lk.user_id == user_id for lk in task.label_keybinds]):
                continue
            # Get the unique set of labels for this task across all previous users
            label_set = list(set([lk.label.lower() for lk in task.label_keybinds]))

            lks_to_create: list[LabelKeybind] = []
            for i, label in enumerate(label_set):
                lks_to_create.append(
                    LabelKeybind(
                        label=label,
                        keybind=constants.DEFAULT_KEYBINDS_IN_ORDER[i],
                        user_id=user_id,
                        task_id=task.id,
                    )
                )

            # The readability of the code below is worth the performance hit (to me) of using
            # create_many multiple times inside the for loop rather than collecting all of the
            # LabelKeybind objects to create and then creating them all at once.
            new_lks.append(
                await label_keybinds_service.create_many(
                    data=lks_to_create, auto_commit=True, auto_expunge=True
                )
            )
            tasks_to_update.append(task)

        for task, lk in zip(tasks_to_update, new_lks, strict=False):
            task.label_keybinds.extend(lk)

        user.assigned_tasks.extend(tasks)
        return Response(content={"message": "Task successfully assigned"}, status_code=HTTP_200_OK)

    @delete(
        path=urls.UNASSIGN_TASK,
        operation_id="unassignTask",
        name="task:unassign_task",
        exclude_from_auth=False,
        summary="Unassign current user from selected task",
        status_code=HTTP_200_OK,
    )
    async def unassign_task(
        self,
        users_service: UserService,
        task_id: str,
        request: Request[User, Any, Any],
    ) -> Response[dict[str, str]] | NotFoundException:
        """Delete a specified task from current user."""
        # TODO: figure out why middleware throws an exception if you run just getting request.user
        user_id = request.user.id
        user = await users_service.get_one(id=user_id)
        bool_mask = [UUID(task_id) == t.id for t in user.assigned_tasks]
        try:
            _ = user.assigned_tasks.pop(bool_mask.index(True))
        except ValueError as exc:
            msg = "Task not found in user's task list"
            raise NotFoundException(msg) from exc

        return Response(content={"message": "Task successfully deleted"}, status_code=HTTP_200_OK)

    @patch(
        path=urls.UPDATE_TASK,
        operation_id="updateTask",
        name="task:update_task",
        exclude_from_auth=False,
        summary="Update task with new keybinds and annotations",
        status_code=HTTP_200_OK,
    )
    async def update_task(  # noqa: PLR0913 (too many arguments 7 > 5)
        self,
        tasks_service: TaskService,
        request: Request[User, Any, Any],
        data: Annotated[TaskUpdateData, Body(media_type=RequestEncodingType.JSON)],
        task_id: UUID,
    ) -> Response[dict[str, str | int]]:
        """Update task with new keybinds and annotations."""
        user_id = request.user.id

        # Update keybinds
        new_lks: list[LabelKeybind] = []
        new_annos: list[Annotation] = []

        for lk in data.label_keybinds:
            new_lks.append(
                LabelKeybind(
                    id=lk["lk_id"],  # type: ignore since we check for presence of id on line 481
                    label=lk["label"],
                    keybind=lk["keybind"],
                    user_id=user_id,
                    task_id=task_id,
                )
                if lk.get("lk_id")
                else LabelKeybind(
                    label=lk["label"],
                    keybind=lk["keybind"],
                    user_id=user_id,
                    task_id=task_id,
                )
            )

        for fp in data.files:
            new_annos.append(
                Annotation(label=None, labeled=False, labeled_by=None, filepath=fp, task_id=task_id)
            )

        await tasks_service.update_task(task_id, user_id, new_lks, new_annos)
        return Response({"content": "success", "status_code": HTTP_200_OK})

    @get(
        path=urls.EXPORT_TASK,
        operation_id="exportTask",
        name="task:export_annotations",
        exclude_from_auth=False,
        summary="Export annotations for task",
        media_type=MediaType.TEXT,
        status_code=HTTP_200_OK,
    )
    async def export_annotations(
        self, users_service: UserService, tasks_service: TaskService, task_id: str
    ) -> Stream:
        task = await tasks_service.get_one(id=task_id)
        title = task.title
        annotations = task.annotations
        labeled_annotations = [a for a in annotations if a.labeled]
        labeled_annotations = sorted(labeled_annotations, key=lambda a: a.id)
        labeled_annotations = [
            {
                "task_title": title,
                "task_id": a.task_id,
                "annotation_id": a.id,
                "labeled_by": (await users_service.get_one(id=a.labeled_by)).username
                if a.labeled_by
                else "Unknown",
                "created_at": a.created_at,
                "updated_at": a.updated_at,
                "filepath": a.filepath,
                "label": a.label,
            }
            for a in labeled_annotations
        ]

        async def iter_content() -> AsyncGenerator[str, None]:
            yield "[\n"
            for i, annotation in enumerate(labeled_annotations):
                jsonified = json.dumps(annotation, indent=4, default=lambda x: str(x))
                # Add a comma to the end if it's not the last item
                jsonified += "," if i < len(labeled_annotations) - 1 else ""
                # Split the JSON string into lines and prepend each line with four spaces
                jsonified = "\n".join("    " + line for line in jsonified.split("\n"))
                yield jsonified + "\n"
            yield "]\n"

        return Stream(
            iter_content(),
            headers={"Content-Disposition": f"attachment; filename={title}_annotations.json"},
        )


class AnnotationController(Controller):
    """Controller for annotation CRUD operations."""

    dependencies = {
        "users_service": Provide(provide_users_service),
        "tasks_service": Provide(provide_tasks_service),
        "annotations_service": Provide(provide_annotations_service),
        "label_keybinds_service": Provide(provide_label_keybinds_service),
    }

    @get(
        path=urls.GET_NEXT_ANNOTATION,
        operation_id="getNextAnnotation",
        name="annotation:get_next",
        exclude_from_auth=False,
        summary="Get next annotation to label",
        status_code=HTTP_200_OK,
    )
    async def get_next_annotation(self, task_id: str, tasks_service: TaskService) -> File:
        task = await tasks_service.get_one(id=task_id)
        unlabeled_annotations = [a for a in task.annotations if not a.labeled]

        if len(unlabeled_annotations) == 0:
            return File(
                path=Path("front/assets/images/task-completed.png").resolve(),
                media_type="image/png",
                headers={"X-Metadata-AnnotationID": "-999"},
            )

        next_annotation = unlabeled_annotations[0]
        return File(
            path=Path(next_annotation.filepath).resolve(),
            media_type="image/png",
            headers={"X-Metadata-AnnotationID": str(next_annotation.id)},
        )

    @get(
        path=urls.GET_ANY_ANNOTATION,
        operation_id="getAnnotation",
        name="annotation:get",
        exclude_from_auth=False,
        summary="Get any annotation, specified by ID",
        status_code=HTTP_200_OK,
    )
    async def get_annotation(
        self, tasks_service: TaskService, task_id: str, annotation_id: str
    ) -> File:
        int_annotation_id = int(annotation_id)
        task = await tasks_service.get_one(id=task_id)
        next_annotations: list[Annotation] = [
            a for a in task.annotations if a.id == int_annotation_id
        ]
        if len(next_annotations) == 0:
            raise PermissionDeniedException("Annotation does not belong to task!")
        next_annotation = next_annotations[0]
        return File(
            path=Path(next_annotation.filepath).resolve(),
            media_type="image/png",
            headers={"X-Metadata-AnnotationID": str(next_annotation.id)},
        )

    @patch(
        path=urls.UPDATE_ANNOTATION,
        operation_id="updateAnnotation",
        name="annotation:update",
        exclude_from_auth=False,
        summary="Update annotation with label from keybind",
        status_code=HTTP_200_OK,
        media_type="application/json",
    )
    async def update(  # noqa: PLR0913 (too many arguments 7 > 5)
        self,
        tasks_service: TaskService,
        annotations_service: AnnotationService,
        data: Annotated[AnnotationUpdateData, Body(media_type=RequestEncodingType.JSON)],
        task_id: str,
        annotation_id: str,
        request: Request[User, Any, Any],
    ) -> dict[str, str | int | float]:
        coerced_annotation_id = int(annotation_id)
        coerced_task_id = UUID(task_id)

        user_tasks = request.user.assigned_tasks
        task = await tasks_service.get_one(id=coerced_task_id)
        if task.id not in [t.id for t in user_tasks]:
            raise PermissionDeniedException("Task does not belong to user!")

        if coerced_annotation_id > 0:  # negative value is sent as response for all annos complete
            annotation = await annotations_service.get_one(id=coerced_annotation_id)
            annotation.label = data.label
            annotation.labeled = bool(data.label)  # if label is empty string or None, it is False
            annotation.labeled_by = request.user.id

        task_annotations = task.annotations
        t1 = len([t for t in task_annotations if t.labeled])
        progress = round(((t1) / (len(task_annotations))) * 100, 2)
        progress = 100 if progress > 100 else progress  # noqa: PLR2004 (replace 100 with const var)

        return {"total": len(task_annotations), "labeled": t1, "progress": progress}


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
    async def check_path(self, path: str) -> Response[dict[str, int]] | NotFoundException:
        """Check if path is directory and get contents information.
        Args:
            path (str): Path to check. Must be an absolute path and must exist on local filesystem.
        Returns:
            Response: Response listing number of files under directory, if it exists.
        """

        if not os.path.exists(path):
            msg = f"Path {path} does not exist"
            raise NotFoundException(msg)

        elif not os.path.isdir(path):
            msg = f"Path {path} is not a directory"
            raise NotFoundException(msg)

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

    @get(
        path=urls.CHECK_HEALTH,
        media_type=MediaType.TEXT,
        operation_id="checkHealth",
        exclude_from_auth=True,
        summary="Test if anything is working",
        status_code=HTTP_200_OK,
    )
    async def check_health(self) -> str:
        return "we are live!"

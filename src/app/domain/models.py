import os
import re
from typing import List, NotRequired, Self, TypedDict
from urllib.parse import unquote
from uuid import UUID

from pydantic import BaseModel, Field, StringConstraints, model_validator
from pydantic.functional_validators import AfterValidator, BeforeValidator
from typing_extensions import Annotated

from app.domain import constants


# USER
class UserData(BaseModel):
    request_username: str
    request_password: str


# ANNOTATION
# class AnnotationUpdate(BaseModel):
#     task_uuid: str
#     annotation_id: int
#     label: str


def validate_path_is_uri_encoded(path: str):
    """
    Validates that the path is URI encoded. URI encoding necessary for ensuring Windows filepaths
    aren't malformed JSON.
    """

    if path == unquote(path):
        raise ValueError("Path is not URI encoded")

    return unquote(path)


def handle_path_escapes(path: str) -> str:
    """
    Escape odd numbered sequences of backslashes by adding one backslash.
    """

    return re.sub(constants.RE_WIN_BACKSLASH, lambda match: match.group() + "\\", path)


def validate_directory_path(path: str) -> str:
    if not os.path.exists(path):
        print(path)
        raise ValueError("Path does not exist")
    elif not os.path.isdir(path):
        print(path)
        raise ValueError("Path is not a directory")

    return path


def validate_path(path: str) -> str:
    if not os.path.exists(path):
        print(path)
        raise ValueError("Path does not exist")

    return path


def validate_keybind(keybind: str) -> str:
    if keybind in ["Shift", "Control", "Alt", "Meta", "z", "Z"]:
        raise ValueError("Keybind is reserved")

    return keybind


ValidURIEncodedDirectoryPath = Annotated[
    str,
    BeforeValidator(handle_path_escapes),
    BeforeValidator(validate_path_is_uri_encoded),
    AfterValidator(validate_directory_path),
]

ValidPath = Annotated[
    str,
    BeforeValidator(handle_path_escapes),
    AfterValidator(validate_path),
]

ValidLabel = Annotated[
    str,
    StringConstraints(min_length=1, max_length=20, pattern=r"^[a-zA-Z0-9\s-]+$"),
    Field(..., description="Label for annotation"),
]
ValidKeybind = Annotated[
    str,
    StringConstraints(max_length=1),
    AfterValidator(validate_keybind),
    Field(..., description="Keybind for label"),
]


class LabelKeybindDict(TypedDict):
    lk_id: NotRequired[UUID]
    label: ValidLabel
    keybind: ValidKeybind


# TASK
class TaskBaseData(BaseModel):
    label_keybinds: List[LabelKeybindDict]

    @model_validator(mode="after")
    def validate_keybinds(self) -> Self:
        labels = [lk["label"] for lk in self.label_keybinds]
        keybinds = [lk["keybind"] for lk in self.label_keybinds]

        if len(labels) != len(set(labels)):
            raise ValueError("Duplicate labels found in keybinds.")
        if len(keybinds) != len(set(keybinds)):
            raise ValueError("Duplicate keybinds found in keybinds.")
        if len(labels) != len(keybinds):
            raise ValueError("Number of labels and keybinds do not match.")

        return self


class TaskData(TaskBaseData):
    title: str = Field(..., max_length=50, description="Title of task")
    root: ValidURIEncodedDirectoryPath


class TaskUpdateData(TaskBaseData):
    files: List[ValidPath] = Field(..., description="Files to be added to task")


# ANNOTATION
class AnnotationUpdateData(BaseModel):
    label: str = Field(..., max_length=20, description="New label assigned to annotation")

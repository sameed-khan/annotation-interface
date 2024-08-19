"""
Options for fixture generation, comes provided with some sensible defaults.
"""

from pathlib import Path
from typing import Self

from pydantic import BaseModel, Field, model_validator


class FixtureOptions(BaseModel):
    overwrite_existing: bool
    num_users: int = Field(..., gt=0)
    num_tasks_per_user: int = Field(..., gt=0)
    assign_same_tasks_to_users: bool
    num_annotations_per_task: int = Field(..., gt=0)
    num_lks_per_user: int
    keybind_set: list[str]
    label_set: list[str]
    fixtures_folder: str
    test_user: dict[str, str | int | float]
    test_task: dict[str, str]

    @model_validator(mode="after")
    def validate_model(self) -> Self:
        if len(self.keybind_set) < self.num_lks_per_user:
            raise ValueError(
                "Size of keybind set less than number of label-keybinds assigned per user"
            )
        if len(self.label_set) < self.num_lks_per_user:
            raise ValueError(
                "Size of label set less than number of label-keybinds assigned per user"
            )

        if self.test_user["id"] != self.test_task["creator_id"]:
            raise ValueError("Test user id does not match test task creator id")

        fixpath: Path = Path(self.fixtures_folder).resolve()
        tfixpath: Path = Path(self.test_task["root_folder"]).resolve()
        if not tfixpath.is_relative_to(fixpath):
            raise ValueError(
                "test task root folder must be subdirectory of annotations_fixtures_folder"
            )

        return self


# Test user has only the test task and no other tasks (to test assignment)
# No other user has the test task
FIXTURE_OPTIONS = FixtureOptions(
    overwrite_existing=False,  # whether to overwrite existing fixtures if already generated
    num_users=4,  # number of users IN ADDITION TO TEST_USER
    num_tasks_per_user=3,  # number of tasks to generate per user, excluding test task
    assign_same_tasks_to_users=False,  # assign every user with the same set of tasks
    num_annotations_per_task=10,  # number of annotations per task
    num_lks_per_user=4,  # number of label-keybind pairs per user
    keybind_set=[  # set of keybinds to select from
        "q",
        "w",
        "e",
        "r",
        "t",
        "y",
        "u",
        "i",
        "o",
        "p",
        "a",
        "s",
        "d",
        "f",
        "j",
        "k",
        "l",
        ";",
        "z",
        "x",
        "c",
        "v",
        "b",
        "n",
        "m",
    ],
    label_set=[  # set of labels to choose from
        "bicep",
        "humerus",
        "deltoid",
        "subscap",
        "femur",
        "sartorius",
        "adductor magnus",
        "glenohumeral joint",
        "tibia",
        "fibula",
        "meniscus",
        "clavicle",
    ],
    fixtures_folder="/home/sameed/projects/hfhs_annotation_interface/src/tests/fixtures",
    test_user={  # a test user that will always be used in all tests
        "id": "233c01cd-0ed1-4a36-a19f-019247a60551",
        "username": "captain_ababo",
        "password": "gravenwind",
        "annotation_rate": 0.0,
    },
    test_task={  # a test task that will the point of reference in all tests
        "id": "7c9b0f02-dc02-47ed-9d3a-3bef365f79c4",
        "title": "When Finish?",
        "root_folder": "/home/sameed/projects/hfhs_annotation_interface/src/tests/fixtures/annotations/test",
        "creator_id": "233c01cd-0ed1-4a36-a19f-019247a60551",
    },
)

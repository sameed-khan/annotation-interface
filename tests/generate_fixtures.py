"""
Simple script to build JSON fixtures given FIXTURE_OPTIONS in adjacent file.
TODO: super slow because generate_random_image just takes a ton of time, probably should make it
just a flat RGB image of some random color rather than being cool and trying to generate a random
texture.
"""

import json
import os
import random
import shutil
import string
import time
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import uuid4

import numpy as np
from fixture_options import FIXTURE_OPTIONS, TestTask, TestUser
from PIL import Image
from tqdm import tqdm


class Case(Enum):
    UPPERCASE = "uppercase"
    LOWERCASE = "lowercase"
    ALL = "all"


def generate_random_image(  # noqa: PLR0913
    filename: str,
    width: int = 1024,
    height: int = 768,
):
    """
    Generate a random RGB image with random colors
    """
    image = Image.new("RGB", (width, height))
    rgb_random = np.stack([np.random.randint(0, 256, (height, width)) for _ in range(3)], axis=2)
    image = Image.fromarray(rgb_random, "RGB")
    image.save(filename, "PNG")


def generate_random_string(length: int = 5, case: Case = Case.ALL) -> str:
    match case:
        case Case.UPPERCASE:
            letters = string.ascii_uppercase
        case Case.LOWERCASE:
            letters = string.ascii_lowercase
        case Case.ALL:
            letters = string.ascii_letters

    return "".join([random.choice(letters) for _ in range(length)])


def generate_unique_dirname(prefix: str = "tmp_", length: int = 5):
    """
    Generate a unique directory name.

    Args:
    prefix (str): A prefix for the directory name. Default is "temp_".
    length (int): Length of the random part of the name. Default is 8.

    Returns:
    str: A unique directory name.
    """

    def base26_encode(number: int):
        """Convert an integer to a base26 string."""
        alphabet = string.ascii_lowercase
        base26 = ""
        while number:
            number, i = divmod(number, 26)
            base26 = alphabet[i] + base26
        return base26 or "a"

    timestamp = base26_encode(int(time.time() * 10000000))  # Get current timestamp in femtoseconds
    random_part = "".join(random.choices(string.ascii_lowercase + string.digits, k=length))

    return f"{prefix}{timestamp}_{random_part}"


def check_is_generated() -> bool:
    """Checks whether fixtures have been generated already"""
    fixtures_folder = Path(FIXTURE_OPTIONS.fixtures_folder).resolve()
    annos_folder = fixtures_folder / Path("annotations")
    if not annos_folder.exists():
        return False

    scopes = ["users", "tasks", "label_keybinds", "annotations", "user_tasks"]
    is_json_generated = all(
        [Path(f"{ fixtures_folder / Path(scope) }.json").exists() for scope in scopes]
    )

    temp: list[bool] = []
    for anno_folder in Path.iterdir(annos_folder):
        temp.append(
            len(list(Path.iterdir(anno_folder))) == FIXTURE_OPTIONS.num_annotations_per_task
        )
    is_annotations_generated = all(temp)

    return is_json_generated and is_annotations_generated


def generate_fixtures() -> None:
    if check_is_generated() and not FIXTURE_OPTIONS.overwrite_existing:
        print("Fixtures already generated, skipping...")
        return

    elif check_is_generated() and FIXTURE_OPTIONS.overwrite_existing:
        print("Overwriting pre-generated fixtures")
        shutil.rmtree(Path(FIXTURE_OPTIONS.fixtures_folder).resolve() / Path("annotations"))
    elif FIXTURE_OPTIONS.overwrite_existing:
        shutil.rmtree(Path(FIXTURE_OPTIONS.fixtures_folder).resolve())
        os.makedirs(Path(FIXTURE_OPTIONS.fixtures_folder).resolve())

    users: list[TestUser] = []
    tasks: list[TestTask] = []
    label_keybinds: list[dict[str, Any]] = []
    annotations: list[dict[str, Any]] = []
    user_tasks: list[dict[str, str]] = []

    annos_folder = Path(FIXTURE_OPTIONS.fixtures_folder).resolve() / Path("annotations")

    # Generate for initial test user
    new_annotations_folder = annos_folder / Path(FIXTURE_OPTIONS.test_task["root_folder"])
    os.makedirs(new_annotations_folder, exist_ok=True)
    users.append(FIXTURE_OPTIONS.test_user)
    tasks.append(FIXTURE_OPTIONS.test_task)
    user_tasks.append({str(FIXTURE_OPTIONS.test_user["id"]): str(FIXTURE_OPTIONS.test_task["id"])})
    label_set = random.sample(FIXTURE_OPTIONS.label_set, FIXTURE_OPTIONS.num_lks_per_user)
    keybind_set = random.sample(FIXTURE_OPTIONS.keybind_set, FIXTURE_OPTIONS.num_lks_per_user)
    label_keybinds.extend(
        [
            {
                "label": label_set[i],
                "keybind": keybind_set[i],
                "user_id": FIXTURE_OPTIONS.test_user["id"],
                "task_id": FIXTURE_OPTIONS.test_task["id"],
            }
            for i in range(FIXTURE_OPTIONS.num_lks_per_user)
        ]
    )
    annotations.extend(
        [
            {
                "label": None,
                "labeled": False,
                "labeled_by": None,
                "filepath": f"{ \
                    new_annotations_folder / Path(generate_unique_dirname(prefix='anno_')) \
                }.png",
                "task_id": FIXTURE_OPTIONS.test_task["id"],
            }
            for _ in range(FIXTURE_OPTIONS.num_annotations_per_task)
        ]
    )
    for anno in annotations:
        generate_random_image(anno["filepath"])

    # Generate for all others
    ## Users
    users.extend(
        [
            {
                "id": str(uuid4()),
                "username": generate_random_string(5, Case.LOWERCASE),
                "password": generate_random_string(5, Case.UPPERCASE),
                "annotation_rate": 0.0,
            }
            for _ in range(FIXTURE_OPTIONS.num_users)
        ]
    )

    for user in tqdm(users[1:], desc="Generating fixtures..."):
        for _ in range(FIXTURE_OPTIONS.num_tasks_per_user):
            newfolder = annos_folder / Path(generate_unique_dirname())
            os.makedirs(newfolder, exist_ok=True)
            local_label_set = random.sample(
                FIXTURE_OPTIONS.label_set, FIXTURE_OPTIONS.num_lks_per_user
            )
            local_keybind_set = random.sample(
                FIXTURE_OPTIONS.keybind_set, FIXTURE_OPTIONS.num_lks_per_user
            )
            new_task = {
                "id": uuid4(),
                "title": generate_random_string(10, Case.UPPERCASE),
                "root_folder": newfolder,
                "creator_id": user["id"],
            }
            tasks.append(new_task)
            user_tasks.append({str(user["id"]): str(new_task["id"])})
            label_keybinds.extend(
                [
                    {
                        "label": local_label_set[i],
                        "keybind": local_keybind_set[i],
                        "user_id": user["id"],
                        "task_id": new_task["id"],
                    }
                    for i in range(FIXTURE_OPTIONS.num_lks_per_user)
                ]
            )

            for _ in range(FIXTURE_OPTIONS.num_annotations_per_task):
                new_anno = {
                    "label": None,
                    "labeled": False,
                    "labeled_by": None,
                    "filepath": f"{newfolder / Path(generate_unique_dirname(prefix='anno_'))}.png",
                    "task_id": new_task["id"],
                }
                annotations.append(new_anno)
                generate_random_image(new_anno["filepath"])  # type: ignore

    user_tasks.extend({str(user["id"]): str(task["id"])} for (user, task) in zip(users, tasks, strict=False))
    all_dicts = [users, tasks, label_keybinds, annotations, user_tasks]
    scopes = ["users", "tasks", "label_keybinds", "annotations", "user_tasks"]
    for data, filename in zip(all_dicts, scopes, strict=False):
        with open(Path(FIXTURE_OPTIONS.fixtures_folder) / Path(f"{filename}.json"), "w") as f:
            json.dump(data, f, indent=4, default=lambda x: str(x))


def teardown_fixtures():
    """Removes all generated fixtures but keeps the folder"""
    shutil.rmtree(Path(FIXTURE_OPTIONS.fixtures_folder).resolve())
    os.makedirs(Path(FIXTURE_OPTIONS.fixtures_folder).resolve())


if __name__ == "__main__":
    os.chdir("/home/sameed/projects/hfhs_annotation_interface")
    generate_fixtures()

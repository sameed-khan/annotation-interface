"""Populate annotations and labelkeybinds test data

Revision ID: 046d4eb2df59
Revises: 80064de40646
Create Date: 2024-06-30 09:50:36.080824

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from pytz import timezone
from sqlalchemy.orm import Session
from uuid import uuid4
from datetime import datetime

from src.app.domain.schema import User, Task, Annotation, LabelKeybind

TEST_USERNAME = "captain_ababo"
TEST_USER_ID = "935afc02-8695-44fc-9e72-fc46c33516a5"

TEST_TASK_ID = "aa715f43-759f-4ed1-9dea-2bcb704fc825"

TEST_ANNO_PATHS = [
    "C:\\Users\\khans24.CC\\Documents\\hfhs_annotation_interface\\static\\assets\\sample\\0000470_diabetes_bicep_sax_source_image.png",
    "C:\\Users\\khans24.CC\\Documents\\hfhs_annotation_interface\\static\\assets\\sample\\0000470_diabetes_supra_lax_source_image.png",
    "C:\\Users\\khans24.CC\\Documents\\hfhs_annotation_interface\\static\\assets\\sample\\1001777_normal_bicep_sax_source_image.png",
    "C:\\Users\\khans24.CC\\Documents\\hfhs_annotation_interface\\static\\assets\\sample\\1001777_normal_supra_lax_source_image.png"
]

TEST_LK_IDS = [
    "9c680f69-02cb-4198-978a-336b675f79bc",
    "ba7c42d0-1da7-4903-a358-ed27c4ecaafb",
    "2e62eb8e-7fe8-439a-b664-18cd3f3b3316",
    "742660e4-9547-44eb-a091-0d37b25a8d90"
]
TEST_LK_LABELS = [
    "Short-Axis Bicep",
    "Short-Axis Supra",
    "Long-Axis Supra",
    "Long-Axis Bicep"
]
TEST_LK_KEYBINDS = ["J", "K", "L", ";"]



# revision identifiers, used by Alembic.
revision: str = '046d4eb2df59'
down_revision: Union[str, None] = '80064de40646'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Assemble annotations
    annotations = []
    label_keybinds = []
    for i in range(len(TEST_ANNO_PATHS)):
        anno = Annotation(
            filepath = TEST_ANNO_PATHS[i],
            labeled = False,
            task_id = TEST_TASK_ID,
            id = i-1,
            created_at = datetime.now(timezone('US/Eastern')),
            updated_at = datetime.now(timezone('US/Eastern'))
        )
        lk = LabelKeybind(
            label = TEST_LK_LABELS[i],
            keybind = TEST_LK_KEYBINDS[i],
            user_id = TEST_USER_ID,
            task_id = TEST_TASK_ID,
            id = TEST_LK_IDS[i],
            created_at = datetime.now(timezone('US/Eastern')),
            updated_at = datetime.now(timezone('US/Eastern'))

        )
        annotations.append(anno)
        label_keybinds.append(lk)

    conn = op.get_bind()
    session = Session(bind=conn)
    session.bulk_save_objects(annotations)
    session.bulk_save_objects(label_keybinds)
    session.commit()

def downgrade() -> None:
    conn = op.get_bind()
    session = Session(bind=conn)
    session.query(Annotation).filter(Annotation.task_id == TEST_TASK_ID).delete()
    session.query(LabelKeybind).filter(LabelKeybind.task_id == TEST_TASK_ID).delete()
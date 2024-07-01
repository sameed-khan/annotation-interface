"""Create test task

Revision ID: bbcd223554eb
Revises: 3236f48525f6
Create Date: 2024-06-30 09:07:41.319078

"""
from uuid import uuid4
from typing import Sequence, Union
from pytz import timezone
from datetime import datetime

from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session

from src.app.domain.schema import User, Task

# revision identifiers, used by Alembic.
revision: str = 'bbcd223554eb'
down_revision: Union[str, None] = '3236f48525f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TEST_TASK_UUID = "aa715f43-759f-4ed1-9dea-2bcb704fc825"


def upgrade() -> None:
    conn = op.get_bind()
    session = Session(bind=conn)

    est = timezone('US/Eastern')
    est_now = datetime.now(est)

    # This depends on revision <base> -> 8b998e42649b, create test user
    original_user = session.query(User).filter(User.username == "captain_ababo").first()
    if original_user is None:
        raise Exception("Original user not found, probably missing migration to create test user")
    
    test_task = Task(
        title="Test Task",
        root_folder="C:\\Users\\khans24.CC\\Documents\\hfhs_annotation_interface\\static\\assets\\sample",
        creator_id=original_user.id,
        id=TEST_TASK_UUID,
        created_at=est_now,
        updated_at=est_now
    )

    session.add(test_task)
    session.commit()

def downgrade() -> None:
    conn = op.get_bind()
    session = Session(bind=conn)

    test_task = session.query(Task).filter(Task.id == TEST_TASK_UUID).first()
    if test_task is not None:
        session.delete(test_task)
        session.commit()
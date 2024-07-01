"""assign user task

Revision ID: fbdfefea95cd
Revises: 046d4eb2df59
Create Date: 2024-06-30 14:59:36.460933

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import select

from pytz import timezone
from sqlalchemy.orm import Session
from uuid import uuid4
from datetime import datetime

from src.app.domain.schema import User, Task, Annotation, LabelKeybind

TEST_USER_ID = "935afc02-8695-44fc-9e72-fc46c33516a5"
TEST_TASK_ID = "aa715f43-759f-4ed1-9dea-2bcb704fc825"

# revision identifiers, used by Alembic.
revision: str = 'fbdfefea95cd'
down_revision: Union[str, None] = '046d4eb2df59'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    session = Session(bind=conn)

    user = session.execute(select(User).where(User.id == TEST_USER_ID)).scalar_one()
    task_to_assign = session.execute(select(Task).where(Task.id == TEST_TASK_ID)).scalar_one()
    user.assigned_tasks.append(task_to_assign)

    session.commit()

def downgrade() -> None:
    conn = op.get_bind()
    session = Session(bind=conn)

    user = session.execute(select(User).where(User.id == TEST_USER_ID)).scalar_one()
    user.assigned_tasks.pop(0)

    session.commit()
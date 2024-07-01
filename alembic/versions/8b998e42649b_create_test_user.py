"""create test user

Revision ID: 8b998e42649b
Revises: 
Create Date: 2024-06-30 07:34:31.776150

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from pytz import timezone
from sqlalchemy.orm import Session
from uuid import uuid4
from datetime import datetime

from src.app.domain.schema import User

# revision identifiers, used by Alembic.
revision: str = '8b998e42649b'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    est = timezone('US/Eastern')
    est_now = datetime.now(est)

    conn = op.get_bind()
    session = Session(bind=conn)

    test_users = [
        User(
            id=uuid4(),
            username="captain_ababo",
            password="abidalikhan",
            annotation_rate=0.0,
            created_at=est_now,
            updated_at=est_now
        ),
        User(
            id=uuid4(),
            username="test",
            password="password",
            annotation_rate=0.0,
            created_at=est_now,
            updated_at=est_now
        )
    ]

    session.add_all(test_users)
    session.commit()

def downgrade() -> None:
    conn = op.get_bind()
    session = Session(bind=conn)

    usernames_to_delete = ["captain_ababo", "test"]
    for username in usernames_to_delete:
        user = session.query(User).filter(User.username == username).first()
        if user:
            session.delete(user)

    session.commit()

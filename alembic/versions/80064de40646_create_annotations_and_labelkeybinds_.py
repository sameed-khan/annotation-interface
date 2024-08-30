"""Create annotations and labelkeybinds tables

Revision ID: 80064de40646
Revises: bbcd223554eb
Create Date: 2024-06-30 09:43:18.524031

"""

from collections.abc import Sequence

import advanced_alchemy
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "80064de40646"
down_revision: str | None = "3236f48525f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "annotations",
        sa.Column("label", sa.String(), nullable=True),
        sa.Column("labeled", sa.Boolean(), nullable=False),
        sa.Column("labeled_by", advanced_alchemy.types.GUID(length=16), nullable=True),
        sa.Column("filepath", sa.String(), nullable=False),
        sa.Column("task_id", advanced_alchemy.types.GUID(length=16), nullable=False),
        sa.Column("id", sa.BigInteger().with_variant(sa.Integer(), "sqlite"), nullable=False),
        sa.Column("created_at", advanced_alchemy.types.DateTimeUTC(timezone=True), nullable=False),
        sa.Column("updated_at", advanced_alchemy.types.DateTimeUTC(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["labeled_by"], ["users.id"], name=op.f("fk_annotations_labeled_by_users")
        ),
        sa.ForeignKeyConstraint(
            ["task_id"], ["tasks.id"], name=op.f("fk_annotations_task_id_tasks")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_annotations")),
        comment="Record of annotation and label",
    )
    op.create_table(
        "label_keybinds",
        sa.Column("label", sa.String(), nullable=False),
        sa.Column("keybind", sa.CHAR(length=1), nullable=False),
        sa.Column("user_id", advanced_alchemy.types.GUID(length=16), nullable=False),
        sa.Column("task_id", advanced_alchemy.types.GUID(length=16), nullable=False),
        sa.Column("id", advanced_alchemy.types.GUID(length=16), nullable=False),
        sa.Column("sa_orm_sentinel", sa.Integer(), nullable=True),
        sa.Column("created_at", advanced_alchemy.types.DateTimeUTC(timezone=True), nullable=False),
        sa.Column("updated_at", advanced_alchemy.types.DateTimeUTC(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["task_id"], ["tasks.id"], name=op.f("fk_label_keybinds_task_id_tasks")
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_label_keybinds_user_id_users")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_label_keybinds")),
        comment="Keybinds specific to a label for a user and task",
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("label_keybinds")
    op.drop_table("annotations")
    # ### end Alembic commands ###

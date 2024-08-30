from uuid import UUID

from advanced_alchemy.base import BigIntAuditBase, UUIDAuditBase
from sqlalchemy import CHAR, Boolean, Column, Float, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Written in this weird way to satisfy mypy
user_id_column: Column[UUID] = Column("user_id", ForeignKey("users.id"), primary_key=True)
task_id_column: Column[UUID] = Column("task_id", ForeignKey("tasks.id"), primary_key=True)
user_tasks = Table("user_tasks", UUIDAuditBase.metadata, user_id_column, task_id_column)


class User(UUIDAuditBase):
    __tablename__ = "users"
    __table_args__ = {"comment": "User accounts"}
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
    annotation_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    created_tasks = relationship("Task", back_populates="creator", lazy="selectin")
    assigned_tasks = relationship(
        "Task", secondary=user_tasks, back_populates="contributors", lazy="selectin"
    )
    label_keybinds = relationship(
        "LabelKeybind", back_populates="user", lazy="selectin", cascade="all, delete-orphan"
    )


class Task(UUIDAuditBase):
    __tablename__ = "tasks"
    __table_args__ = {"comment": "Tasks for annotating data"}
    title: Mapped[str] = mapped_column(String, nullable=False)
    root_folder: Mapped[str] = mapped_column(String, nullable=False)
    creator_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))

    creator = relationship("User", back_populates="created_tasks", lazy="joined")
    contributors = relationship(
        "User",
        secondary=user_tasks,
        back_populates="assigned_tasks",
        lazy="selectin",
    )
    annotations = relationship(
        "Annotation",
        back_populates="associated_task",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    label_keybinds = relationship(
        "LabelKeybind", back_populates="task", lazy="selectin", cascade="all, delete-orphan"
    )


class Annotation(BigIntAuditBase):
    __tablename__ = "annotations"
    __table_args__ = {"comment": "Record of annotation and label"}
    label: Mapped[str | None] = mapped_column(String, nullable=True)
    labeled: Mapped[bool] = mapped_column(Boolean, nullable=False)
    labeled_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    filepath: Mapped[str] = mapped_column(String, nullable=False)
    task_id: Mapped[UUID] = mapped_column(ForeignKey("tasks.id"), nullable=False)

    associated_task = relationship("Task", back_populates="annotations", lazy="joined")


class LabelKeybind(UUIDAuditBase):
    __tablename__ = "label_keybinds"
    __table_args__ = {"extend_existing": True}
    label: Mapped[str] = mapped_column(String, nullable=False)
    keybind: Mapped[str] = mapped_column(CHAR(1), nullable=False)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    task_id: Mapped[UUID] = mapped_column(ForeignKey("tasks.id"))

    user = relationship("User", back_populates="label_keybinds", lazy="joined")
    task = relationship("Task", back_populates="label_keybinds", lazy="joined")

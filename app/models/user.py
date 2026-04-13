from __future__ import annotations

from typing import List, Optional

from sqlalchemy import Boolean, CheckConstraint, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("char_length(trim(name)) > 0", name="ck_users_name_not_blank"),
        CheckConstraint("position('@' in email) > 1", name="ck_users_email_has_at"),
        CheckConstraint("semester IS NULL OR semester >= 1", name="ck_users_semester_positive"),
    )

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    semester: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")

    professions: Mapped[List["UserProfession"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    skills: Mapped[List["UserSkill"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    courses: Mapped[List["UserCourse"]] = relationship(back_populates="user", cascade="all, delete-orphan")

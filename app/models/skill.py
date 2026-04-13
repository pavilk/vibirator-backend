from __future__ import annotations

from enum import Enum as PyEnum
from typing import List

from sqlalchemy import CheckConstraint, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SkillLevel(PyEnum):
    BEGINNER = "beginner"
    ELEMENTARY = "elementary"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class Skill(Base):
    __tablename__ = "skills"
    __table_args__ = (
        CheckConstraint("char_length(trim(name)) > 0", name="ck_skills_name_not_blank"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)

    users: Mapped[List["UserSkill"]] = relationship(back_populates="skill", cascade="all, delete-orphan")
    professions: Mapped[List["ProfessionSkill"]] = relationship(back_populates="skill", cascade="all, delete-orphan")
    courses: Mapped[List["CourseSkill"]] = relationship(back_populates="skill", cascade="all, delete-orphan")

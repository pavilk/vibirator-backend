from __future__ import annotations

from typing import Optional

from sqlalchemy import Boolean, CheckConstraint, Enum, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.skill import SkillLevel


class UserProfession(Base):
    __tablename__ = "user_profession"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )
    profession_id: Mapped[int] = mapped_column(
        ForeignKey("professions.id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )

    user: Mapped["User"] = relationship(back_populates="professions")
    profession: Mapped["Profession"] = relationship(back_populates="users")


class UserSkill(Base):
    __tablename__ = "user_skills"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )
    skill_id: Mapped[int] = mapped_column(
        ForeignKey("skills.id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )
    level: Mapped[SkillLevel] = mapped_column(
        Enum(SkillLevel, name="skill_level_enum"),
        nullable=False,
        default=SkillLevel.BEGINNER,
    )

    user: Mapped["User"] = relationship(back_populates="skills")
    skill: Mapped["Skill"] = relationship(back_populates="users")


class UserCourse(Base):
    __tablename__ = "user_courses"
    __table_args__ = (
        UniqueConstraint("user_id", "position", name="uq_user_courses_user_position"),
        CheckConstraint("position IS NULL OR position >= 1", name="ck_user_courses_position_positive"),
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )
    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )
    position: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    user: Mapped["User"] = relationship(back_populates="courses")
    course: Mapped["Course"] = relationship(back_populates="users")


class ProfessionSkill(Base):
    __tablename__ = "profession_skill"
    __table_args__ = (
        CheckConstraint(
            "weight >= 1",
            name="ck_profession_skill_weight_positive",
        ),
        CheckConstraint(
            "display_order IS NULL OR display_order >= 0",
            name="ck_profession_skill_display_order_non_negative",
        ),
    )

    profession_id: Mapped[int] = mapped_column(
        ForeignKey("professions.id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )
    skill_id: Mapped[int] = mapped_column(
        ForeignKey("skills.id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )
    weight: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    show: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    display_order: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    extra: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")

    profession: Mapped["Profession"] = relationship(back_populates="skills")
    skill: Mapped["Skill"] = relationship(back_populates="professions")


class CourseSkill(Base):
    __tablename__ = "course_skill"

    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )
    skill_id: Mapped[int] = mapped_column(
        ForeignKey("skills.id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )
    from_level: Mapped[SkillLevel] = mapped_column(
        Enum(SkillLevel, name="course_skill_from_level_enum"),
        nullable=False,
    )
    to_level: Mapped[SkillLevel] = mapped_column(
        Enum(SkillLevel, name="course_skill_to_level_enum"),
        nullable=False,
    )

    course: Mapped["Course"] = relationship(back_populates="skills")
    skill: Mapped["Skill"] = relationship(back_populates="courses")

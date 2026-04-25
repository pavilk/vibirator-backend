from __future__ import annotations

from typing import List, Optional

from sqlalchemy import Boolean, CheckConstraint, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Course(Base):
    __tablename__ = "courses"
    __table_args__ = (
        CheckConstraint("char_length(trim(title)) > 0", name="ck_courses_title_not_blank"),
        CheckConstraint("char_length(trim(platform)) > 0", name="ck_courses_platform_not_blank"),
        CheckConstraint("char_length(trim(url)) > 0", name="ck_courses_url_not_blank"),
        CheckConstraint("char_length(trim(description)) > 0", name="ck_courses_description_not_blank"),
        CheckConstraint("rating IS NULL OR (rating >= 0 AND rating <= 5)", name="ck_courses_rating_range"),
        CheckConstraint("practices_count IS NULL OR practices_count >= 0", name="ck_courses_practices_count_non_negative"),
        CheckConstraint("z_e IS NULL OR z_e >= 0", name="ck_courses_ze_non_negative"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    platform: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    rating: Mapped[Optional[float]] = mapped_column(Numeric(3, 1), nullable=True)
    practices_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    workload_raw: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_online: Mapped[bool] = mapped_column(Boolean, nullable=False)
    z_e: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_paid: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    target_years: Mapped[Optional[list[int]]] = mapped_column(PG_ARRAY(Integer), nullable=True)
    semesters: Mapped[Optional[list[int]]] = mapped_column(PG_ARRAY(Integer), nullable=True)

    users: Mapped[List["UserCourse"]] = relationship(back_populates="course", cascade="all, delete-orphan")
    skills: Mapped[List["CourseSkill"]] = relationship(back_populates="course", cascade="all, delete-orphan")

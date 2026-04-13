from __future__ import annotations

from typing import List, Optional

from sqlalchemy import CheckConstraint, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Profession(Base):
    __tablename__ = "professions"
    __table_args__ = (
        CheckConstraint("char_length(trim(title)) > 0", name="ck_professions_title_not_blank"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    users: Mapped[List["UserProfession"]] = relationship(back_populates="profession", cascade="all, delete-orphan")
    skills: Mapped[List["ProfessionSkill"]] = relationship(back_populates="profession", cascade="all, delete-orphan")

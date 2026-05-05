"""Роутер подбора курсов для пользователя."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session
from app.models.profession import Profession
from app.models.skill import Skill
from app.models.user import User
from app.schemas.matching import RecommendationResponse, SkillCoursesResponse
from app.services.course_matching import get_best_courses_for_user, get_courses_for_skill

router = APIRouter()


@router.get("/professions/{profession_id}", response_model=RecommendationResponse)
async def match_profession_courses(
    profession_id: int,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> RecommendationResponse:
    """Возвращает лучший курс для каждого навыка выбранной профессии."""
    prof = await session.get(Profession, profession_id)
    if prof is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profession not found",
        )
    return await get_best_courses_for_user(
        session, current_user.user_id, profession_id
    )


@router.get("/skills/{skill_id}", response_model=SkillCoursesResponse)
async def match_skill_courses(
    skill_id: int,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> SkillCoursesResponse:
    """Возвращает два списка курсов для навыка (UrFU и остальные)."""
    skill = await session.get(Skill, skill_id)
    if skill is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found",
        )
    return await get_courses_for_skill(
        session, current_user.user_id, skill_id
    )

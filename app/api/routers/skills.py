from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session, require_admin
from app.models.skill import Skill
from app.models.user import User
from app.schemas.skill import SkillCreate, SkillRead, SkillUpdate

router = APIRouter()


@router.get("/", response_model=list[SkillRead])
async def list_skills(
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> list[Skill]:
    result = await session.execute(select(Skill).order_by(Skill.id))
    return list(result.scalars().all())


@router.get("/{skill_id}", response_model=SkillRead)
async def get_skill(
    skill_id: int,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> Skill:
    skill = await session.get(Skill, skill_id)
    if skill is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")
    return skill


@router.post("/", response_model=SkillRead, status_code=status.HTTP_201_CREATED)
async def create_skill(
    payload: SkillCreate,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_admin),
) -> Skill:
    existing_skill = await session.execute(select(Skill).where(Skill.name == payload.name))
    if existing_skill.scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Skill with this name already exists")

    skill = Skill(**payload.model_dump())
    session.add(skill)
    await session.commit()
    await session.refresh(skill)
    return skill


@router.patch("/{skill_id}", response_model=SkillRead)
async def update_skill(
    skill_id: int,
    payload: SkillUpdate,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_admin),
) -> Skill:
    skill = await session.get(Skill, skill_id)
    if skill is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")

    update_data = payload.model_dump(exclude_unset=True)
    if "name" in update_data:
        existing_skill = await session.execute(
            select(Skill).where(Skill.name == update_data["name"], Skill.id != skill_id)
        )
        if existing_skill.scalar_one_or_none() is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Skill with this name already exists")

    for field, value in update_data.items():
        setattr(skill, field, value)

    await session.commit()
    await session.refresh(skill)
    return skill


@router.delete("/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_skill(
    skill_id: int,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_admin),
) -> None:
    skill = await session.get(Skill, skill_id)
    if skill is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")

    await session.delete(skill)
    await session.commit()

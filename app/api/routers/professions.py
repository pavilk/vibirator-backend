from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session, require_admin
from app.models.profession import Profession
from app.models.user import User
from app.schemas.profession import ProfessionCreate, ProfessionRead, ProfessionUpdate

router = APIRouter()


@router.get("/", response_model=list[ProfessionRead])
async def list_professions(
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> list[Profession]:
    result = await session.execute(select(Profession).order_by(Profession.id))
    return list(result.scalars().all())


@router.get("/{profession_id}", response_model=ProfessionRead)
async def get_profession(
    profession_id: int,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> Profession:
    profession = await session.get(Profession, profession_id)
    if profession is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profession not found")
    return profession


@router.post("/", response_model=ProfessionRead, status_code=status.HTTP_201_CREATED)
async def create_profession(
    payload: ProfessionCreate,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_admin),
) -> Profession:
    profession = Profession(**payload.model_dump())
    session.add(profession)
    await session.commit()
    await session.refresh(profession)
    return profession


@router.patch("/{profession_id}", response_model=ProfessionRead)
async def update_profession(
    profession_id: int,
    payload: ProfessionUpdate,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_admin),
) -> Profession:
    profession = await session.get(Profession, profession_id)
    if profession is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profession not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profession, field, value)

    await session.commit()
    await session.refresh(profession)
    return profession


@router.delete("/{profession_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profession(
    profession_id: int,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_admin),
) -> None:
    profession = await session.get(Profession, profession_id)
    if profession is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profession not found")

    await session.delete(profession)
    await session.commit()

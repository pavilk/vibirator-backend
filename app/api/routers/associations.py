from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import Select, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session, require_admin
from app.models.associations import (
    CourseSkill,
    ProfessionSkill,
    UserCourse,
    UserProfession,
    UserSkill,
)
from app.models.course import Course
from app.models.profession import Profession
from app.models.skill import Skill
from app.models.user import User
from app.schemas.association import (
    CourseSkillCreate,
    CourseSkillRead,
    CourseSkillUpdate,
    ProfessionSkillCreate,
    ProfessionSkillRead,
    ProfessionSkillUpdate,
    UserCourseCreate,
    UserCourseRead,
    UserCourseUpdate,
    UserProfessionCreate,
    UserProfessionRead,
    UserSkillCreate,
    UserSkillRead,
    UserSkillUpdate,
)

router = APIRouter()


async def ensure_exists(
    session: AsyncSession,
    model: type[Any],
    entity_id: int,
    label: str,
) -> None:
    entity = await session.get(model, entity_id)
    if entity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{label} not found")


async def commit_or_409(session: AsyncSession, detail: str) -> None:
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail) from None


@router.get("/user-professions", response_model=list[UserProfessionRead])
async def list_user_professions(
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> list[UserProfession]:
    result = await session.execute(
        select(UserProfession).order_by(UserProfession.user_id, UserProfession.profession_id)
    )
    return list(result.scalars().all())


@router.post(
    "/user-professions",
    response_model=UserProfessionRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_user_profession(
    payload: UserProfessionCreate,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_admin),
) -> UserProfession:
    await ensure_exists(session, User, payload.user_id, "User")
    await ensure_exists(session, Profession, payload.profession_id, "Profession")

    item = UserProfession(**payload.model_dump())
    session.add(item)
    await commit_or_409(session, "This user profession link already exists")
    return item


@router.delete(
    "/user-professions/{user_id}/{profession_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_user_profession(
    user_id: int,
    profession_id: int,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_admin),
) -> None:
    item = await session.get(UserProfession, {"user_id": user_id, "profession_id": profession_id})
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User profession link not found")

    await session.delete(item)
    await session.commit()


@router.get("/user-skills", response_model=list[UserSkillRead])
async def list_user_skills(
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> list[UserSkill]:
    result = await session.execute(select(UserSkill).order_by(UserSkill.user_id, UserSkill.skill_id))
    return list(result.scalars().all())


@router.post("/user-skills", response_model=UserSkillRead, status_code=status.HTTP_201_CREATED)
async def create_user_skill(
    payload: UserSkillCreate,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_admin),
) -> UserSkill:
    await ensure_exists(session, User, payload.user_id, "User")
    await ensure_exists(session, Skill, payload.skill_id, "Skill")

    item = UserSkill(**payload.model_dump())
    session.add(item)
    await commit_or_409(session, "This user skill link already exists")
    return item


@router.patch("/user-skills/{user_id}/{skill_id}", response_model=UserSkillRead)
async def update_user_skill(
    user_id: int,
    skill_id: int,
    payload: UserSkillUpdate,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_admin),
) -> UserSkill:
    item = await session.get(UserSkill, {"user_id": user_id, "skill_id": skill_id})
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User skill link not found")

    item.level = payload.level
    await session.commit()
    await session.refresh(item)
    return item


@router.delete("/user-skills/{user_id}/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_skill(
    user_id: int,
    skill_id: int,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_admin),
) -> None:
    item = await session.get(UserSkill, {"user_id": user_id, "skill_id": skill_id})
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User skill link not found")

    await session.delete(item)
    await session.commit()


@router.get("/user-courses", response_model=list[UserCourseRead])
async def list_user_courses(
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> list[UserCourse]:
    result = await session.execute(select(UserCourse).order_by(UserCourse.user_id, UserCourse.course_id))
    return list(result.scalars().all())


@router.post("/user-courses", response_model=UserCourseRead, status_code=status.HTTP_201_CREATED)
async def create_user_course(
    payload: UserCourseCreate,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_admin),
) -> UserCourse:
    await ensure_exists(session, User, payload.user_id, "User")
    await ensure_exists(session, Course, payload.course_id, "Course")

    item = UserCourse(**payload.model_dump())
    session.add(item)
    await commit_or_409(session, "This user course link or position already exists")
    return item


@router.patch("/user-courses/{user_id}/{course_id}", response_model=UserCourseRead)
async def update_user_course(
    user_id: int,
    course_id: int,
    payload: UserCourseUpdate,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_admin),
) -> UserCourse:
    item = await session.get(UserCourse, {"user_id": user_id, "course_id": course_id})
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User course link not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)

    await commit_or_409(session, "This course position is already used by the user")
    await session.refresh(item)
    return item


@router.delete("/user-courses/{user_id}/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_course(
    user_id: int,
    course_id: int,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_admin),
) -> None:
    item = await session.get(UserCourse, {"user_id": user_id, "course_id": course_id})
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User course link not found")

    await session.delete(item)
    await session.commit()


@router.get("/profession-skills", response_model=list[ProfessionSkillRead])
async def list_profession_skills(
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> list[ProfessionSkill]:
    result = await session.execute(
        select(ProfessionSkill).order_by(ProfessionSkill.profession_id, ProfessionSkill.skill_id)
    )
    return list(result.scalars().all())


@router.post(
    "/profession-skills",
    response_model=ProfessionSkillRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_profession_skill(
    payload: ProfessionSkillCreate,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_admin),
) -> ProfessionSkill:
    await ensure_exists(session, Profession, payload.profession_id, "Profession")
    await ensure_exists(session, Skill, payload.skill_id, "Skill")

    item = ProfessionSkill(**payload.model_dump())
    session.add(item)
    await commit_or_409(session, "This profession skill link already exists")
    return item


@router.patch("/profession-skills/{profession_id}/{skill_id}", response_model=ProfessionSkillRead)
async def update_profession_skill(
    profession_id: int,
    skill_id: int,
    payload: ProfessionSkillUpdate,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_admin),
) -> ProfessionSkill:
    item = await session.get(
        ProfessionSkill,
        {"profession_id": profession_id, "skill_id": skill_id},
    )
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profession skill link not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    await session.commit()
    await session.refresh(item)
    return item


@router.delete(
    "/profession-skills/{profession_id}/{skill_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_profession_skill(
    profession_id: int,
    skill_id: int,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_admin),
) -> None:
    item = await session.get(
        ProfessionSkill,
        {"profession_id": profession_id, "skill_id": skill_id},
    )
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profession skill link not found")

    await session.delete(item)
    await session.commit()


@router.get("/course-skills", response_model=list[CourseSkillRead])
async def list_course_skills(
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> list[CourseSkill]:
    result = await session.execute(select(CourseSkill).order_by(CourseSkill.course_id, CourseSkill.skill_id))
    return list(result.scalars().all())


@router.post("/course-skills", response_model=CourseSkillRead, status_code=status.HTTP_201_CREATED)
async def create_course_skill(
    payload: CourseSkillCreate,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_admin),
) -> CourseSkill:
    await ensure_exists(session, Course, payload.course_id, "Course")
    await ensure_exists(session, Skill, payload.skill_id, "Skill")

    item = CourseSkill(**payload.model_dump())
    session.add(item)
    await commit_or_409(session, "This course skill link already exists")
    return item


@router.patch("/course-skills/{course_id}/{skill_id}", response_model=CourseSkillRead)
async def update_course_skill(
    course_id: int,
    skill_id: int,
    payload: CourseSkillUpdate,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_admin),
) -> CourseSkill:
    item = await session.get(CourseSkill, {"course_id": course_id, "skill_id": skill_id})
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course skill link not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)

    await session.commit()
    await session.refresh(item)
    return item


@router.delete("/course-skills/{course_id}/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_course_skill(
    course_id: int,
    skill_id: int,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_admin),
) -> None:
    item = await session.get(CourseSkill, {"course_id": course_id, "skill_id": skill_id})
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course skill link not found")

    await session.delete(item)
    await session.commit()

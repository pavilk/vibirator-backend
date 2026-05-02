from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
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
from app.models.skill import Skill, SkillLevel
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


SKILL_LEVEL_ORDER: dict[SkillLevel, int] = {
    SkillLevel.BEGINNER: 0,
    SkillLevel.INTERMEDIATE: 1,
    SkillLevel.ADVANCED: 2,
}


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


def ensure_self_or_admin(current_user: User, user_id: int, action: str) -> None:
    if current_user.is_admin or current_user.user_id == user_id:
        return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=f"You can only {action} for yourself",
    )


async def get_user_course_by_skill_or_course(
    session: AsyncSession,
    user_id: int,
    skill_or_course_id: int,
) -> UserCourse | None:
    item = await session.get(UserCourse, {"user_id": user_id, "skill_id": skill_or_course_id})
    if item is not None:
        return item

    result = await session.execute(
        select(UserCourse)
        .where(
            UserCourse.user_id == user_id,
            UserCourse.course_id == skill_or_course_id,
        )
        .order_by(UserCourse.skill_id)
        .limit(1)
    )
    return result.scalar_one_or_none()


def parse_skill_level(value: str) -> SkillLevel:
    try:
        return SkillLevel(value.lower())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Course skill target level is invalid",
        ) from None


async def update_user_skill_after_completed_course(
    session: AsyncSession,
    item: UserCourse,
) -> None:
    course_skill = await session.get(
        CourseSkill,
        {"course_id": item.course_id, "skill_id": item.skill_id},
    )
    if course_skill is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Course skill target level is not configured",
        )

    target_level = parse_skill_level(course_skill.to_level)
    user_skill = await session.get(
        UserSkill,
        {"user_id": item.user_id, "skill_id": item.skill_id},
    )
    if user_skill is None:
        session.add(
            UserSkill(
                user_id=item.user_id,
                skill_id=item.skill_id,
                level=target_level,
            )
        )
        return

    if SKILL_LEVEL_ORDER[target_level] > SKILL_LEVEL_ORDER[user_skill.level]:
        user_skill.level = target_level


async def ensure_course_matches_skill(
    session: AsyncSession,
    course_id: int,
    skill_id: int,
) -> None:
    course_skill = await session.get(
        CourseSkill,
        {"course_id": course_id, "skill_id": skill_id},
    )
    if course_skill is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course is not linked to this skill",
        )


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
    current_user: User = Depends(get_current_user),
) -> UserProfession:
    await ensure_exists(session, Profession, payload.profession_id, "Profession")

    if payload.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only add a profession for yourself",
        )

    existing_item = await session.get(
        UserProfession,
        {"user_id": payload.user_id, "profession_id": payload.profession_id},
    )
    if existing_item is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This user profession link already exists",
        )

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
    current_user: User = Depends(get_current_user),
) -> None:
    ensure_self_or_admin(current_user, user_id, "delete a profession link")

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
    current_user: User = Depends(get_current_user),
) -> UserSkill:
    await ensure_exists(session, Skill, payload.skill_id, "Skill")

    if payload.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only add a skill for yourself",
        )

    existing_item = await session.get(
        UserSkill,
        {"user_id": payload.user_id, "skill_id": payload.skill_id},
    )
    if existing_item is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This user skill link already exists",
        )

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
    current_user: User = Depends(get_current_user),
) -> UserSkill:
    ensure_self_or_admin(current_user, user_id, "update a skill link")

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
    current_user: User = Depends(get_current_user),
) -> None:
    ensure_self_or_admin(current_user, user_id, "delete a skill link")

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
    result = await session.execute(select(UserCourse).order_by(UserCourse.user_id, UserCourse.skill_id))
    return list(result.scalars().all())


@router.post("/user-courses", response_model=UserCourseRead, status_code=status.HTTP_201_CREATED)
async def create_user_course(
    payload: UserCourseCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> UserCourse:
    await ensure_exists(session, Skill, payload.skill_id, "Skill")
    await ensure_exists(session, Course, payload.course_id, "Course")

    if payload.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only add a course for yourself",
        )

    existing_item = await session.get(
        UserCourse,
        {"user_id": payload.user_id, "skill_id": payload.skill_id},
    )
    if existing_item is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This user course link already exists",
        )

    item = UserCourse(**payload.model_dump())
    session.add(item)
    await commit_or_409(session, "This user course link already exists")
    return item


@router.patch("/user-courses/{user_id}/{skill_id}", response_model=UserCourseRead)
async def update_user_course(
    user_id: int,
    skill_id: int,
    payload: UserCourseUpdate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> UserCourse:
    ensure_self_or_admin(current_user, user_id, "update a course link")

    item = await get_user_course_by_skill_or_course(session, user_id, skill_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User course link not found")

    update_data = payload.model_dump(exclude_unset=True)
    if "course_id" in update_data:
        await ensure_course_matches_skill(session, update_data["course_id"], item.skill_id)
        if update_data["course_id"] != item.course_id and "is_completed" not in update_data:
            item.is_completed = False

    for field, value in update_data.items():
        setattr(item, field, value)

    if payload.is_completed is True:
        await update_user_skill_after_completed_course(session, item)

    await commit_or_409(session, "This user course link already exists")
    await session.refresh(item)
    return item


@router.delete("/user-courses/{user_id}/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_course(
    user_id: int,
    skill_id: int,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> None:
    ensure_self_or_admin(current_user, user_id, "delete a course link")

    item = await get_user_course_by_skill_or_course(session, user_id, skill_id)
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

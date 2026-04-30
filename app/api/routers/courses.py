from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session, require_admin
from app.models.course import Course
from app.models.user import User
from app.models.associations import CourseSkill
from app.schemas.course import CourseCreate, CourseRead, CourseUpdate
from app.schemas.matching import UserSkillPlanResponse
from app.services.course_matching import get_or_create_user_skill_plan

router = APIRouter()


@router.get("/", response_model=list[CourseRead])
async def list_courses(
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> list[Course]:
    result = await session.execute(select(Course).order_by(Course.id))
    return list(result.scalars().all())


@router.get("/plan", response_model=UserSkillPlanResponse)
async def get_user_plan(
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> UserSkillPlanResponse:
    return await get_or_create_user_skill_plan(session, current_user.user_id)


@router.get("/{course_id}", response_model=CourseRead)
async def get_course(
    course_id: int,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> Course:
    course = await session.get(Course, course_id)
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    return course

@router.get("/skills/{skill_id}", response_model=list[CourseRead])
async def get_courses_by_skill(
    skill_id: int,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> list[CourseRead]:
    query = (
        select(Course)
        .join(CourseSkill, CourseSkill.course_id == Course.id)
        .where(CourseSkill.skill_id == skill_id)
    )
    result = await session.execute(query)
    courses = result.scalars().all()
    if not courses:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Courses not found for this skill",
        )
    return list(courses)


@router.post("/", response_model=CourseRead, status_code=status.HTTP_201_CREATED)
async def create_course(
    payload: CourseCreate,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_admin),
) -> Course:
    course = Course(**payload.model_dump(mode="python"))
    session.add(course)
    await session.commit()
    await session.refresh(course)
    return course


@router.patch("/{course_id}", response_model=CourseRead)
async def update_course(
    course_id: int,
    payload: CourseUpdate,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_admin),
) -> Course:
    course = await session.get(Course, course_id)
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    for field, value in payload.model_dump(exclude_unset=True, mode="python").items():
        setattr(course, field, value)

    await session.commit()
    await session.refresh(course)
    return course


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_course(
    course_id: int,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_admin),
) -> None:
    course = await session.get(Course, course_id)
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    await session.delete(course)
    await session.commit()

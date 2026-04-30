"""
Сервис подбора курсов.

Функции:
- get_best_courses_for_user — для каждого навыка профессии подобрать один лучший курс
- get_courses_for_skill   — для конкретного навыка вернуть два списка: UrFU и остальные
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.associations import CourseSkill, ProfessionSkill, UserCourse, UserProfession, UserSkill
from app.models.course import Course
from app.models.skill import Skill, SkillLevel
from app.models.user import User
from app.schemas.course import CourseRead
from app.schemas.matching import (
    RecommendationResponse,
    ScoredCourseRead,
    SkillCoursesResponse,
    SkillRecommendation,
    UserSkillPlanItem,
    UserSkillPlanResponse,
)

LEVEL_ORDER: dict[SkillLevel, int] = {
    SkillLevel.BEGINNER: 0,
    SkillLevel.INTERMEDIATE: 1,
    SkillLevel.ADVANCED: 2,
}

URFU_PLATFORM = "UrFU"


def _compute_score(
    course: Course,
    cs: CourseSkill,
    user_level: SkillLevel,
    user: User | None = None,
    is_urfu_mode: bool = False,
) -> float:
    """
    Вычисляет релевантность курса для пользователя.

    Формула состоит из нескольких компонентов:

    1. Совпадение уровня (0–50 баллов)
       - from_level == user_level  → 50  (курс начинается ровно с уровня юзера)
       - from_level ≤ user_level ≤ to_level → 35  (юзер внутри диапазона курса)
       - from_level < user_level, но to_level < user_level →
             max(0, 15 - (user_level - to_level) * 10)
             (курс ниже уровня юзера — менее полезен)
       - from_level > user_level →
             max(0, 20 - (from_level - user_level) * 15)
             (курс выше уровня юзера — сложнее)

    2. Сохранённый relevance_score из course_skill (0–100 баллов)
       Это значение, заполненное при наполнении БД.

    3. Бонус за рейтинг курса (0–25 баллов)
       rating * 5  (рейтинг от 0 до 5)

    4. Бонус за бесплатность (0 или 20 баллов, только для НЕ-UrFU курсов)
       На UrFU все курсы бесплатные, поэтому бонус не нужен.
       Для остальных платформ бесплатный курс с хорошим рейтингом
       должен быть ближе к топу.

    5. UrFU-бонусы (только для курсов UrFU при is_urfu_mode=True):
       - Совпадение course_year юзера с target_years курса → +15
         Соседний год (±1) → +5
       - Совпадение semester юзера с semesters курса → +10

       У курсов не с UrFU поля z_e, target_years, semesters = NULL,
       поэтому эти бонусы для них никогда не начисляются.

    Фильтрация UrFU-курсов:
       Если course_year и semester юзера старше всех доступных
       target_years и semesters курса, такой курс полностью исключается
       (возвращается None из _compute_score_or_none).
    """
    score = 0.0

    user_lvl = LEVEL_ORDER[user_level]
    from_lvl = LEVEL_ORDER.get(cs.from_level, 0)
    to_lvl = LEVEL_ORDER.get(cs.to_level, 2)

    if from_lvl == user_lvl:
        score += 50.0
    elif from_lvl <= user_lvl <= to_lvl:
        score += 35.0
    elif from_lvl < user_lvl:
        score += max(0.0, 15.0 - (user_lvl - to_lvl) * 10.0)
    else:
        score += max(0.0, 20.0 - (from_lvl - user_lvl) * 15.0)

    if cs.relevance_score is not None:
        score += min(cs.relevance_score, 100)

    if course.rating is not None:
        score += float(course.rating) * 5.0

    if not is_urfu_mode and course.is_paid is not None and not course.is_paid:
        score += 20.0

    if is_urfu_mode and user is not None:
        if user.course_year and course.target_years:
            if user.course_year in course.target_years:
                score += 15.0
            else:
                min_diff = min(abs(user.course_year - y) for y in course.target_years)
                if min_diff == 1:
                    score += 5.0

        if user.semester and course.semesters:
            if user.semester in course.semesters:
                score += 10.0

    return round(score, 2)


def _is_urfu_course_relevant(course: Course, user: User) -> bool:
    """
    Проверяет, актуален ли UrFU-курс для студента.

    Если у юзера указаны course_year и semester, а у курса заполнены
    target_years и/или semesters, то курс исключается если юзер
    «старше» всех доступных значений (уже прошёл этот этап обучения).
    """
    if user.course_year and course.target_years:
        if user.course_year > max(course.target_years):
            return False

    if user.semester and course.semesters:
        if user.semester > max(course.semesters):
            return False

    return True


def _course_to_scored(course: Course, skill_id: int, score: float) -> ScoredCourseRead:
    """Конвертация ORM-модели Course в Pydantic-схему ScoredCourseRead."""
    return ScoredCourseRead(
        id=course.id,
        title=course.title,
        platform=course.platform,
        url=course.url,
        description=course.description,
        rating=float(course.rating) if course.rating is not None else None,
        practices_count=course.practices_count,
        workload_raw=course.workload_raw,
        is_online=course.is_online,
        z_e=course.z_e,
        is_paid=course.is_paid,
        target_years=course.target_years,
        semesters=course.semesters,
        skill_id=skill_id,
        score=score,
    )


def _course_to_read(course: Course) -> CourseRead:
    return CourseRead.model_validate(course)


def _scored_to_course_read(course: ScoredCourseRead) -> CourseRead:
    return CourseRead(
        id=course.id,
        title=course.title,
        platform=course.platform,
        url=course.url,
        description=course.description,
        rating=course.rating,
        practices_count=course.practices_count,
        workload_raw=course.workload_raw,
        is_online=course.is_online,
        z_e=course.z_e,
        is_paid=course.is_paid,
        target_years=course.target_years,
        semesters=course.semesters,
    )


async def _load_profession_context(
    session: AsyncSession,
    user_id: int,
    profession_id: int,
) -> tuple[User, list[ProfessionSkill], dict[int, SkillLevel], dict[int, list[CourseSkill]], dict[int, str]]:
    """
    Загружает всё необходимое для подбора курсов:
    - пользователя
    - навыки профессии (с порядком)
    - уровни юзера в этих навыках
    - связи курс-навык (с подгруженными курсами)
    - имена навыков
    """
    user = await session.get(User, user_id)
    if user is None:
        raise ValueError(f"Пользователь {user_id} не найден")

    prof_skills_q = (
        select(ProfessionSkill)
        .where(ProfessionSkill.profession_id == profession_id)
        .order_by(
            ProfessionSkill.display_order.asc().nullslast(),
        )
    )
    prof_skills = list((await session.execute(prof_skills_q)).scalars().all())

    if not prof_skills:
        return user, [], {}, {}, {}

    skill_ids = [ps.skill_id for ps in prof_skills]

    us_q = select(UserSkill).where(
        UserSkill.user_id == user_id,
        UserSkill.skill_id.in_(skill_ids),
    )
    user_skill_map: dict[int, SkillLevel] = {
        us.skill_id: us.level
        for us in (await session.execute(us_q)).scalars().all()
    }

    cs_q = (
        select(CourseSkill)
        .where(CourseSkill.skill_id.in_(skill_ids))
        .options(selectinload(CourseSkill.course))
    )
    all_cs = list((await session.execute(cs_q)).scalars().all())
    cs_by_skill: dict[int, list[CourseSkill]] = {}
    for cs in all_cs:
        cs_by_skill.setdefault(cs.skill_id, []).append(cs)

    sk_q = select(Skill).where(Skill.id.in_(skill_ids))
    skill_name_map: dict[int, str] = {
        s.id: s.name for s in (await session.execute(sk_q)).scalars().all()
    }

    return user, prof_skills, user_skill_map, cs_by_skill, skill_name_map


async def get_best_courses_for_user(
    session: AsyncSession,
    user_id: int,
    profession_id: int,
) -> RecommendationResponse:
    """
    Для каждого навыка профессии подбирает один лучший (дефолтный) курс.

    Логика для FIIT-студентов:
    - Сначала ищем лучший UrFU-курс (с UrFU-бонусами за course_year/semester).
    - Если UrFU-курс найден → он становится дефолтным.
    - Если UrFU-курсов для этого навыка нет → берём лучший из остальных платформ.

    Для обычных пользователей:
    - Просто лучший курс из всех платформ по базовой формуле.

    Порядок навыков определяется полем display_order из таблицы profession_skill.
    """
    user, prof_skills, user_skill_map, cs_by_skill, skill_name_map = (
        await _load_profession_context(session, user_id, profession_id)
    )

    if not prof_skills:
        return RecommendationResponse(
            user_id=user_id,
            profession_id=profession_id,
            recommendations=[],
        )

    recommendations: list[SkillRecommendation] = []

    for ps in prof_skills:
        sid = ps.skill_id
        user_level = user_skill_map.get(sid, SkillLevel.BEGINNER)
        skill_name = skill_name_map.get(sid, "")
        candidates = cs_by_skill.get(sid, [])

        best_course: ScoredCourseRead | None = None

        if user.is_fiit:
            urfu_best: ScoredCourseRead | None = None
            urfu_best_score = -1.0

            for cs in candidates:
                course = cs.course
                if course.platform != URFU_PLATFORM:
                    continue
                if not _is_urfu_course_relevant(course, user):
                    continue
                sc = _compute_score(course, cs, user_level, user=user, is_urfu_mode=True)
                if sc > urfu_best_score:
                    urfu_best_score = sc
                    urfu_best = _course_to_scored(course, sid, sc)

            if urfu_best is not None:
                best_course = urfu_best
            else:
                other_best_score = -1.0
                for cs in candidates:
                    course = cs.course
                    sc = _compute_score(course, cs, user_level)
                    if sc > other_best_score:
                        other_best_score = sc
                        best_course = _course_to_scored(course, sid, sc)
        else:
            best_score = -1.0
            for cs in candidates:
                course = cs.course
                sc = _compute_score(course, cs, user_level)
                if sc > best_score:
                    best_score = sc
                    best_course = _course_to_scored(course, sid, sc)

        recommendations.append(
            SkillRecommendation(
                skill_id=sid,
                skill_name=skill_name,
                user_level=user_level.value,
                recommended_course=best_course,
            )
        )

    return RecommendationResponse(
        user_id=user_id,
        profession_id=profession_id,
        recommendations=recommendations,
    )


async def get_courses_for_skill(
    session: AsyncSession,
    user_id: int,
    skill_id: int,
) -> SkillCoursesResponse:
    """
    Возвращает все курсы для данного навыка, разделённые на два списка:

    - urfu_courses  — курсы с платформы UrFU (только для FIIT-студентов),
                      отсортированные по UrFU-формуле (с бонусами за course_year/semester).
                      Для не-FIIT юзеров = None.
    - other_courses — все остальные курсы (не UrFU), отсортированные по базовой формуле.
                      Для не-FIIT юзеров — вообще все курсы (включая UrFU).

    Курсы UrFU и остальные никогда не смешиваются в одном списке для FIIT-юзеров.
    """
    user = await session.get(User, user_id)
    if user is None:
        raise ValueError(f"Пользователь {user_id} не найден")

    user_skill = await session.get(UserSkill, {"user_id": user_id, "skill_id": skill_id})
    user_level = user_skill.level if user_skill else SkillLevel.BEGINNER

    skill = await session.get(Skill, skill_id)
    skill_name = skill.name if skill else ""

    cs_q = (
        select(CourseSkill)
        .where(CourseSkill.skill_id == skill_id)
        .options(selectinload(CourseSkill.course))
    )
    course_skills = list((await session.execute(cs_q)).scalars().all())

    if user.is_fiit:
        urfu_scored: list[ScoredCourseRead] = []
        other_scored: list[ScoredCourseRead] = []

        for cs in course_skills:
            course = cs.course
            if course.platform == URFU_PLATFORM:
                if not _is_urfu_course_relevant(course, user):
                    continue
                sc = _compute_score(course, cs, user_level, user=user, is_urfu_mode=True)
                urfu_scored.append(_course_to_scored(course, skill_id, sc))
            else:
                sc = _compute_score(course, cs, user_level)
                other_scored.append(_course_to_scored(course, skill_id, sc))

        urfu_scored.sort(key=lambda c: c.score, reverse=True)
        other_scored.sort(key=lambda c: c.score, reverse=True)

        return SkillCoursesResponse(
            skill_id=skill_id,
            skill_name=skill_name,
            user_level=user_level.value,
            urfu_courses=urfu_scored,
            other_courses=other_scored,
        )
    else:
        all_scored: list[ScoredCourseRead] = []
        for cs in course_skills:
            course = cs.course
            sc = _compute_score(course, cs, user_level)
            all_scored.append(_course_to_scored(course, skill_id, sc))

        all_scored.sort(key=lambda c: c.score, reverse=True)

        return SkillCoursesResponse(
            skill_id=skill_id,
            skill_name=skill_name,
            user_level=user_level.value,
            urfu_courses=None,
            other_courses=all_scored,
        )


async def get_or_create_user_skill_plan(
    session: AsyncSession,
    user_id: int,
) -> UserSkillPlanResponse:
    """
    Возвращает по одному курсу на каждый навык, который выбрал пользователь.

    Если для навыка уже есть запись в user_courses, она используется как кэш.
    Если записи нет, сервис подбирает лучший курс для этого навыка, сохраняет
    его в user_courses и возвращает вместе с остальными рекомендациями.
    """
    user_skills_q = (
        select(UserSkill)
        .where(UserSkill.user_id == user_id)
        .options(selectinload(UserSkill.skill))
        .order_by(UserSkill.skill_id)
    )
    user_skills = list((await session.execute(user_skills_q)).scalars().all())

    if not user_skills:
        return UserSkillPlanResponse(user_id=user_id, recommendations=[])

    existing_q = (
        select(UserCourse)
        .where(UserCourse.user_id == user_id)
        .options(selectinload(UserCourse.course))
        .order_by(UserCourse.skill_id)
    )
    existing_items = list((await session.execute(existing_q)).scalars().all())
    existing_by_skill = {item.skill_id: item for item in existing_items}

    recommendations: list[UserSkillPlanItem] = []
    new_links: list[UserCourse] = []

    for user_skill in user_skills:
        existing_item = existing_by_skill.get(user_skill.skill_id)
        if existing_item is not None:
            recommendations.append(
                UserSkillPlanItem(
                    skill_id=user_skill.skill_id,
                    skill_name=user_skill.skill.name,
                    user_level=user_skill.level.value,
                    planned_course=_course_to_read(existing_item.course),
                )
            )
            continue

        skill_courses = await get_courses_for_skill(session, user_id, user_skill.skill_id)

        selected_course: ScoredCourseRead | None = None
        if skill_courses.urfu_courses:
            selected_course = skill_courses.urfu_courses[0]
        elif skill_courses.other_courses:
            selected_course = skill_courses.other_courses[0]

        if selected_course is not None:
            new_links.append(
                UserCourse(
                    user_id=user_id,
                    skill_id=user_skill.skill_id,
                    course_id=selected_course.id,
                    is_completed=False,
                )
            )

        recommendations.append(
            UserSkillPlanItem(
                skill_id=user_skill.skill_id,
                skill_name=user_skill.skill.name,
                user_level=user_skill.level.value,
                planned_course=(
                    _scored_to_course_read(selected_course)
                    if selected_course is not None
                    else None
                ),
            )
        )

    if new_links:
        session.add_all(new_links)
        await session.commit()

    return UserSkillPlanResponse(user_id=user_id, recommendations=recommendations)

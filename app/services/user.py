from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.associations import UserSkill, UserCourse, UserProfession

class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user(self, id: int) -> User:
        result = await self.db.execute(select(User).where(User.user_id == id))
        return result.scalar_one_or_none()



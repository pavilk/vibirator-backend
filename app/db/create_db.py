import asyncio

import app.models  # noqa: F401
from app.db.base import Base
from app.db.session import engine


async def create_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await engine.dispose()
    print("Database tables created successfully")


if __name__ == "__main__":
    asyncio.run(create_db())

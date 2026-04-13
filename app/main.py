from fastapi import FastAPI

from app.api.routers import associations, auth, courses, professions, skills, users

app = FastAPI(title="Vibirator Backend")

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(skills.router, prefix="/skills", tags=["skills"])
app.include_router(courses.router, prefix="/courses", tags=["courses"])
app.include_router(professions.router, prefix="/professions", tags=["professions"])
app.include_router(associations.router, prefix="/relations", tags=["relations"])


@app.get("/health", tags=["health"])
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}

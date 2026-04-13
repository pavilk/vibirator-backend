from pydantic import BaseModel, ConfigDict, Field


class ProfessionBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None


class ProfessionCreate(ProfessionBase):
    pass


class ProfessionUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None


class ProfessionRead(ProfessionBase):
    model_config = ConfigDict(from_attributes=True)

    id: int

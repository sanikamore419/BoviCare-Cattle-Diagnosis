from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field


class CattleBase(BaseModel):
    tag_number: str = Field(min_length=1, max_length=80)
    name: str | None = Field(default=None, max_length=120)
    breed: str | None = Field(default=None, max_length=100)
    date_of_birth: str | None = Field(default=None, description="ISO date string YYYY-MM-DD")
    sex: Literal["female", "male", "unknown"] = "unknown"
    weight_kg: float | None = Field(default=None, ge=0, le=2000)


class CattleCreate(CattleBase):
    pass


class CattleUpdate(BaseModel):
    tag_number: str | None = Field(default=None, min_length=1, max_length=80)
    name: str | None = Field(default=None, max_length=120)
    breed: str | None = None
    date_of_birth: str | None = None
    sex: Literal["female", "male", "unknown"] | None = None
    weight_kg: float | None = Field(default=None, ge=0, le=2000)


class CattleRead(CattleBase):
    id: int
    farmer_id: int
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}

from datetime import datetime

from pydantic import BaseModel


class BaseMCPCreate(BaseModel):
    name: str
    description: str | None = None


class BaseMCPUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class BaseMCP(BaseModel):
    id: int | None = None
    name: str | None = None
    description: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

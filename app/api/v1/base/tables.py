from datetime import datetime, timezone

from sqlmodel import Field, SQLModel

from .models import BaseMCP as BaseMCPModel


class BaseMCPTable(BaseMCPModel, SQLModel):
    id: int | None = Field(default=None, primary_key=True)
    name: str | None = Field(default=None)
    description: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

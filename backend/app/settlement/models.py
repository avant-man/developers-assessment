import uuid
from datetime import datetime

from sqlmodel import Field, SQLModel


class Record(SQLModel, table=True):
    """
    Single-table model for all settlement domain entities.

    type: worklog | segment | adjustment | remittance | settlement_line
    parent_id: self-referential FK for hierarchy
    user_id: FK to user table (set on worklog and remittance records)
    data: JSON blob with type-specific fields
    """

    __tablename__ = "record"

    id: int | None = Field(default=None, primary_key=True)
    type: str = Field(max_length=64, index=True)
    parent_id: int | None = Field(default=None, foreign_key="record.id", index=True)
    user_id: uuid.UUID | None = Field(default=None, foreign_key="user.id", index=True)
    data: str = Field(default="{}")
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime | None = Field(default=None)

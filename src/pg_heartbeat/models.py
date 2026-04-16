from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel


class Heartbeat(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    service: str = Field(index=True)
    instance_id: Optional[str] = Field(default=None, index=True)
    status: str = Field(default="ok")
    message: Optional[str] = None
    hostname: Optional[str] = None
    version: Optional[str] = None
    uptime_seconds: Optional[float] = None
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    metadata_json: Optional[str] = Field(default=None, description="JSON-encoded extra metadata")

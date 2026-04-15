from __future__ import annotations

import json
import socket
from datetime import datetime, timezone
from typing import Any, Optional, Sequence

from sqlalchemy import Engine
from sqlmodel import Session, SQLModel, create_engine, select

from .models import Heartbeat


def create_tables(engine_or_url: Engine | str, echo: bool = False) -> None:
    """Create heartbeat tables. Call once at app startup."""
    if isinstance(engine_or_url, Engine):
        engine = engine_or_url
    else:
        engine = create_engine(engine_or_url, echo=echo)
    SQLModel.metadata.create_all(engine)


class HeartbeatHandle:
    """Simple client for pushing and querying heartbeat records."""

    def __init__(self, engine: Engine, service: str, version: Optional[str] = None, instance_id: Optional[str] = None) -> None:
        self.engine = engine
        self.service = service
        self.version = version
        self.instance_id = instance_id
        self.hostname = socket.gethostname()
        self._started_at = datetime.now(timezone.utc)

    def beat(
        self,
        service: Optional[str] = None,
        status: str = "ok",
        message: Optional[str] = None,
        hostname: Optional[str] = None,
        version: Optional[str] = None,
        instance_id: Optional[str] = None,
        uptime_seconds: Optional[float] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> Heartbeat:
        """Record a heartbeat for a service."""
        service = service or self.service
        heartbeat = Heartbeat(
            service=service,
            instance_id=instance_id or self.instance_id,
            status=status,
            message=message,
            hostname=hostname or self.hostname,
            version=version or self.version,
            uptime_seconds=uptime_seconds if uptime_seconds is not None else (datetime.now(timezone.utc) - self._started_at).total_seconds(),
            timestamp=datetime.now(timezone.utc),
            metadata_json=json.dumps(metadata) if metadata else None,
        )
        with Session(self.engine) as session:
            session.add(heartbeat)
            session.commit()
            session.refresh(heartbeat)
        return heartbeat

    def latest(self, service: Optional[str] = None) -> Optional[Heartbeat]:
        """Get the most recent heartbeat for a service."""
        service = service or self.service
        with Session(self.engine) as session:
            statement = (
                select(Heartbeat)
                .where(Heartbeat.service == service)
                .order_by(Heartbeat.timestamp.desc())  # type: ignore[union-attr]
                .limit(1)
            )
            if self.instance_id:
                statement = statement.where(Heartbeat.instance_id == self.instance_id)
            return session.exec(statement).first()

    def history(
        self,
        service: Optional[str] = None,
        limit: int = 100,
        since: Optional[datetime] = None,
    ) -> Sequence[Heartbeat]:
        """Get heartbeat history for a service."""
        service = service or self.service
        with Session(self.engine) as session:
            statement = (
                select(Heartbeat)
                .where(Heartbeat.service == service)
                .order_by(Heartbeat.timestamp.desc())  # type: ignore[union-attr]
                .limit(limit)
            )
            if self.instance_id:
                statement = statement.where(Heartbeat.instance_id == self.instance_id)
            if since:
                statement = statement.where(Heartbeat.timestamp >= since)
            return session.exec(statement).all()

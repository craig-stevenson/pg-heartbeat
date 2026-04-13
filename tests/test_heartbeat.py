import json
import time

from sqlmodel import create_engine
from pg_heartbeat import HeartbeatHandle, create_tables


def _setup(service: str = "svc") -> HeartbeatHandle:
    engine = create_engine("sqlite://")
    create_tables(engine)
    return HeartbeatHandle(engine, service=service)


def test_beat_and_latest():
    db = _setup("my-api")
    db.beat(status="ok", message="all good")
    hb = db.latest()
    assert hb is not None
    assert hb.service == "my-api"
    assert hb.status == "ok"
    assert hb.message == "all good"


def test_history():
    db = _setup()
    db.beat(message="first")
    db.beat(message="second")
    db.beat(message="third")
    records = db.history()
    assert len(records) == 3
    assert records[0].message == "third"  # most recent first


def test_metadata_round_trip():
    db = _setup()
    input_metadata = {"version": "1.2.3", "uptime": 42, "tags": ["web", "prod"]}
    db.beat(metadata=input_metadata)
    hb = db.latest()
    assert hb is not None
    assert hb.metadata_json is not None
    parsed = json.loads(hb.metadata_json)
    assert parsed == input_metadata


def test_latest_returns_none_for_unknown():
    db = _setup()
    assert db.latest() is None


def test_service_override():
    db = _setup("default-svc")
    db.beat()
    db.beat(service="other-svc")
    assert db.latest().service == "default-svc"
    assert db.latest(service="other-svc").service == "other-svc"

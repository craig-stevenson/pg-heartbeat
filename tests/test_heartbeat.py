import json
import time

from sqlmodel import create_engine
from pg_heartbeat import HeartbeatHandle, create_tables


def _make_engine():
    engine = create_engine("sqlite://")
    create_tables(engine)
    return engine


def _setup(service: str = "svc", **kwargs) -> HeartbeatHandle:
    engine = _make_engine()
    return HeartbeatHandle(engine, service=service, **kwargs)


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


def test_instance_id():
    engine = _make_engine()
    db1 = HeartbeatHandle(engine, service="my-api", instance_id="replica-1")
    db2 = HeartbeatHandle(engine, service="my-api", instance_id="replica-2")
    db1.beat(message="from replica 1")
    db2.beat(message="from replica 2")
    hb1 = db1.latest()
    hb2 = db2.latest()
    assert hb1.instance_id == "replica-1"
    assert hb1.message == "from replica 1"
    assert hb2.instance_id == "replica-2"
    assert hb2.message == "from replica 2"


def test_timestamp_is_set():
    db = _setup()
    db.beat()
    hb = db.latest()
    assert hb is not None
    assert hb.timestamp is not None

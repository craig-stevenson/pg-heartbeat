import json
import subprocess
import time

import pytest
from sqlmodel import create_engine

from pg_heartbeat import HeartbeatHandle, create_tables

CONTAINER_NAME = "pg_heartbeat_test"
PG_USER = "testuser"
PG_PASS = "testpass"
PG_DB = "testdb"
PG_PORT = 15432
PG_URL = f"postgresql://{PG_USER}:{PG_PASS}@localhost:{PG_PORT}/{PG_DB}"


@pytest.fixture(scope="module")
def pg_engine():
    """Start a Postgres container, yield an engine, then tear down."""
    # Remove any leftover container
    subprocess.run(["docker", "rm", "-f", CONTAINER_NAME], capture_output=True)

    subprocess.run(
        [
            "docker", "run", "-d",
            "--name", CONTAINER_NAME,
            "-e", f"POSTGRES_USER={PG_USER}",
            "-e", f"POSTGRES_PASSWORD={PG_PASS}",
            "-e", f"POSTGRES_DB={PG_DB}",
            "-p", f"{PG_PORT}:5432",
            "postgres:17",
        ],
        check=True,
    )

    # Wait for Postgres to be ready
    engine = create_engine(PG_URL)
    for _ in range(30):
        try:
            with engine.connect() as conn:
                conn.exec_driver_sql("SELECT 1")
            break
        except Exception:
            time.sleep(1)
    else:
        raise RuntimeError("Postgres did not become ready in time")

    create_tables(engine)
    yield engine

    subprocess.run(["docker", "rm", "-f", CONTAINER_NAME], capture_output=True)


def test_beat_and_latest(pg_engine):
    db = HeartbeatHandle(pg_engine, service="pg-api")
    db.beat(status="ok", message="hello postgres")
    hb = db.latest()
    assert hb is not None
    assert hb.service == "pg-api"
    assert hb.status == "ok"
    assert hb.message == "hello postgres"
    assert hb.hostname is not None


def test_history(pg_engine):
    db = HeartbeatHandle(pg_engine, service="pg-history")
    db.beat(message="first")
    db.beat(message="second")
    db.beat(message="third")
    records = db.history()
    assert len(records) == 3
    assert records[0].message == "third"


def test_metadata_round_trip(pg_engine):
    db = HeartbeatHandle(pg_engine, service="pg-meta")
    input_metadata = {"version": "1.2.3", "uptime": 42, "tags": ["web", "prod"]}
    db.beat(metadata=input_metadata)
    hb = db.latest()
    assert hb is not None
    parsed = json.loads(hb.metadata_json)
    assert parsed == input_metadata


def test_version_and_uptime(pg_engine):
    db = HeartbeatHandle(pg_engine, service="pg-version", version="2.0.0")
    db.beat()
    hb = db.latest()
    assert hb is not None
    assert hb.version == "2.0.0"
    assert hb.uptime_seconds >= 0


def test_service_override(pg_engine):
    db = HeartbeatHandle(pg_engine, service="pg-default")
    db.beat()
    db.beat(service="pg-other")
    assert db.latest().service == "pg-default"
    assert db.latest(service="pg-other").service == "pg-other"


def test_latest_returns_none_for_unknown(pg_engine):
    db = HeartbeatHandle(pg_engine, service="pg-ghost")
    assert db.latest() is None


def test_timestamp_is_timezone_aware(pg_engine):
    db = HeartbeatHandle(pg_engine, service="pg-tz")
    db.beat()
    hb = db.latest()
    assert hb is not None
    assert hb.timestamp.tzinfo is not None

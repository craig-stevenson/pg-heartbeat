# pg-heartbeat

A simple way for Python applications to push heartbeat info to a SQL database.

## Installation

```bash
pip install pg-heartbeat
```

## Quick Start

```python
from sqlmodel import create_engine
from pg_heartbeat import HeartbeatHandle, create_tables

engine = create_engine("postgresql://user:pass@localhost/mydb")

# Create tables once at app startup
create_tables(engine)

# Create a client
db = HeartbeatHandle(engine, service="my-service", version="1.0.0")

# Send a heartbeat
db.beat()

# Send with details
db.beat(status="ok", message="Processed 42 items", metadata={"queue_depth": 12})

# Get the latest heartbeat
latest = db.latest()
print(f"{latest.service} at {latest.timestamp}: {latest.status}")

# Get history
for hb in db.history(limit=10):
    print(f"{hb.timestamp}: {hb.status} - {hb.message}")
```

### Override service per call

You can query or record heartbeats for a different service by passing `service` to any method:

```python
db = HeartbeatHandle(engine, service="api-server")
db.beat()                              # records for "api-server"
db.latest(service="worker")            # queries "worker" instead
```

## API

### `create_tables(engine_or_url, echo=False)`

Create the heartbeat tables. Call once at app startup. Accepts a database URL string or an existing SQLAlchemy `Engine`.

### `HeartbeatHandle(engine, service, version=None)`

Create a client. Accepts a SQLAlchemy `Engine`.

The following fields are auto-populated on every `beat()` call:
- **hostname** — looked up via `socket.gethostname()` at init
- **version** — set from the constructor argument
- **uptime_seconds** — seconds since the `HeartbeatHandle` instance was created

### `db.beat(service=None, status="ok", message=None, hostname=None, version=None, uptime_seconds=None, metadata=None)`

Record a heartbeat. Returns the `Heartbeat` row. Auto-populated fields (`hostname`, `version`, `uptime_seconds`) can be overridden per call.

`metadata` accepts a dict that is stored as JSON.

### `db.latest(service=None)`

Get the most recent heartbeat for a service, or `None`.

### `db.history(service=None, limit=100, since=None)`

Get recent heartbeats, newest first. Optionally filter by a `since` datetime.

## Database Support

Works with any database supported by SQLAlchemy — SQLite, PostgreSQL, MySQL, etc. Install the appropriate driver:

```bash
pip install pg-heartbeat psycopg2-binary  # PostgreSQL
pip install pg-heartbeat pymysql           # MySQL
```

## License

MIT

# pg-heartbeat

A simple way for Python applications to push heartbeat info to a SQL database.

## Installation

```bash
pip install pg-heartbeat
```

## Quick Start

```python
from sqlmodel import create_engine
from pg_heartbeat import PgHeartbeat, create_tables

engine = create_engine("sqlite:///heartbeats.db")

# Create tables once at app startup
create_tables(engine)

# Create a client
db = PgHeartbeat(engine, service="my-service")

# Send a heartbeat
db.beat()

# Send with details
db.beat(status="ok", message="Processed 42 items", metadata={"version": "1.2.3"})

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
db = PgHeartbeat(engine, service="api-server")
db.beat()                              # records for "api-server"
db.latest(service="worker")            # checks "worker" instead
```

## API

### `create_tables(engine_or_url, echo=False)`

Create the heartbeat tables. Call once at app startup. Accepts a database URL or an existing SQLAlchemy `Engine`.

### `PgHeartbeat(engine, service)`

Create a client. Accepts a SQLAlchemy `Engine`.

### `db.beat(service=None, status="ok", message=None, metadata=None)`

Record a heartbeat. Returns the `Heartbeat` row.

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

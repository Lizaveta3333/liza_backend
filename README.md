# Liza Backend

FastAPI backend for marketplace application with PostgreSQL, JWT auth, and Kafka integration.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables (optional)
export DATABASE_URL="postgresql+asyncpg://user:pass@localhost/db"
export KAFKA_BOOTSTRAP_SERVERS="localhost:9092"

# Run server
uvicorn app.main:app --reload
```

API docs: `http://localhost:8000/docs`

## Features

- **Auth**: JWT-based authentication (RS256)
- **CRUD**: Users, Products, Orders
- **Kafka**: Event streaming for order events
- **Database**: Async PostgreSQL with SQLAlchemy

## Testing

```bash
pytest -v
```

## Tech Stack

FastAPI, SQLAlchemy (async), PostgreSQL, Kafka, JWT (RS256), Pytest


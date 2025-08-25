# Gravity Curve - Backend (FastAPI)

FastAPI-based backend for the Gravity Curve game. Supports:
- User profile management
- Score submission and retrieval
- Leaderboard (global and per-level)
- Game progress save/load
- OpenAPI documentation and CORS configuration
- SQLite (default) or PostgreSQL (via SQLAlchemy)

## Requirements

- Python 3.10+
- See requirements.txt for Python dependencies.

## Setup

1. Create a virtual environment and install dependencies:

   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
   pip install -r requirements.txt

2. Create a `.env` file based on `.env.example` if you want to override defaults:

   cp .env.example .env
   # Edit as needed

3. Run the development server:

   uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

4. Open docs:

- Swagger UI: http://localhost:8000/docs
- OpenAPI JSON: http://localhost:8000/openapi.json

## Environment Variables

- DATABASE_URL: SQLAlchemy database URL (default: sqlite:///./gravity_curve.db)
- DB_ECHO: Set "true" to echo SQL for debugging.

PostgreSQL example:
postgresql+psycopg2://user:password@localhost:5432/gravity_curve

## API Overview

- GET /               -> Health check
- GET /docs/websocket -> Future WebSocket usage notes

Users
- POST /users
- GET  /users
- GET  /users/{user_id}
- PATCH /users/{user_id}
- DELETE /users/{user_id}

Scores
- POST /scores
- GET  /scores/user/{user_id}
- GET  /scores/level/{level}

Leaderboard
- GET /leaderboard/global
- GET /leaderboard/level/{level}

Progress
- POST   /progress          (upsert)
- GET    /progress/{user_id}/{level}
- DELETE /progress/{user_id}/{level}

## Notes

- This scaffold auto-creates tables on startup. For production, add Alembic migrations.
- Game progress is stored as JSON string for portability between SQLite and Postgres.
- Leaderboard uses a simple aggregation by ranking on points, moves, and duration.


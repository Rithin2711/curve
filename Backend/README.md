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

## Quickstart

1) Create and activate a virtual environment then install dependencies:

   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
   pip install -r requirements.txt

2) Configure environment (optional). Copy the example file:

   cp .env.example .env
   # Edit .env to suit your environment

3) Run the development server:

   uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

4) Explore API docs:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

## Environment Variables

- DATABASE_URL: SQLAlchemy database URL (default: sqlite:///./gravity_curve.db)
- DB_ECHO: Set "true" to echo SQL for debugging
- CORS_ALLOW_ORIGINS: Comma-separated origins or "*" to allow all

PostgreSQL example:
postgresql+psycopg2://user:password@localhost:5432/gravity_curve

## Project structure

- src/api/main.py              -> FastAPI app, routes, models, schemas
- src/api/generate_openapi.py  -> Writes interfaces/openapi.json
- interfaces/openapi.json      -> Generated spec (run the script to create)
- requirements.txt             -> Python dependencies

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

- Tables are auto-created on startup for development. For production, add Alembic migrations.
- Game progress is stored as a JSON string for portability between SQLite and Postgres.
- Leaderboard uses ordering by points (desc), moves (asc), duration (asc).
- The service is designed to be consumed by a React frontend (CORS is enabled).

## Export OpenAPI

To generate an OpenAPI spec file locally:

   python -m src.api.generate_openapi

This creates interfaces/openapi.json which can be used by other services/clients.

## Linting (CI-friendly)

You can lint the codebase without relying on a specific virtualenv path:

- Using Makefile:
  
  make lint

- Or directly:

  bash scripts/lint.sh

These commands will ensure flake8 is available (installed to user site-packages if necessary) and run it using the .flake8 configuration.

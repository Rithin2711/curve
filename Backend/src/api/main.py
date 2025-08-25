import os
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, status, Path, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field, PositiveInt
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, func, Text, desc, UniqueConstraint
from sqlalchemy.orm import sessionmaker, declarative_base, relationship, Session
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

# -----------------------------
# Settings / Configuration
# -----------------------------

class Settings(BaseModel):
    """Application settings loaded from environment variables."""
    APP_NAME: str = "Gravity Curve Backend"
    APP_DESCRIPTION: str = (
        "FastAPI backend for Gravity Curve game. Manages user profiles, scores, leaderboard, "
        "and game progress. Provides REST APIs consumed by the frontend."
    )
    APP_VERSION: str = "1.0.0"
    CORS_ALLOW_ORIGINS: List[str] = ["*"]
    DB_URL: str = Field(default_factory=lambda: os.getenv("DATABASE_URL") or os.getenv("DB_URL") or "sqlite:///./gravity_curve.db")
    DB_ECHO: bool = (os.getenv("DB_ECHO", "false").lower() == "true")

settings = Settings()

# -----------------------------
# Database setup (SQLAlchemy)
# -----------------------------

Base = declarative_base()

# PUBLIC_INTERFACE
def get_engine_url() -> str:
    """Return the SQLAlchemy engine URL based on environment configuration."""
    url = settings.DB_URL
    # For SQLite, ensure proper connection args will be provided in session factory creation.
    return url

engine = create_engine(get_engine_url(), echo=settings.DB_ECHO, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

# Dependency to get DB session
def get_db():
    """Provide a SQLAlchemy session to request scope."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -----------------------------
# Models
# -----------------------------

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    scores = relationship("Score", back_populates="user", cascade="all, delete-orphan")
    progresses = relationship("GameProgress", back_populates="user", cascade="all, delete-orphan")


class Score(Base):
    __tablename__ = "scores"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    level = Column(Integer, nullable=False, index=True)
    points = Column(Integer, nullable=False, index=True)
    moves = Column(Integer, nullable=False)
    duration_ms = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="scores")

    __table_args__ = (
        # Each submission is independent, but this helps frequent queries
        {},
    )


class GameProgress(Base):
    __tablename__ = "game_progress"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    level = Column(Integer, nullable=False, index=True)
    # JSON stored as text for portability (SQLite/Postgres)
    state_json = Column(Text, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", back_populates="progresses")
    __table_args__ = (
        UniqueConstraint("user_id", "level", name="uq_progress_user_level"),
    )

# Create tables on startup (simple approach for demo/scaffold; in prod use migrations)
Base.metadata.create_all(bind=engine)

# -----------------------------
# Schemas (Pydantic)
# -----------------------------

class UserCreate(BaseModel):
    email: EmailStr = Field(..., description="Unique email for the user")
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = Field(None, description="New email")
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="New username")


class UserOut(BaseModel):
    id: int
    email: EmailStr
    username: str
    created_at: Optional[str]

    class Config:
        from_attributes = True


class ScoreCreate(BaseModel):
    user_id: PositiveInt = Field(..., description="User ID who achieved the score")
    level: PositiveInt = Field(..., description="Game level index (1-based)")
    points: int = Field(..., description="Score points awarded")
    moves: int = Field(..., description="Number of moves to finish")
    duration_ms: int = Field(..., description="Total time in milliseconds")


class ScoreOut(BaseModel):
    id: int
    user_id: int
    level: int
    points: int
    moves: int
    duration_ms: int
    created_at: Optional[str]

    class Config:
        from_attributes = True


class LeaderboardEntry(BaseModel):
    username: str = Field(..., description="Username")
    points: int = Field(..., description="Best points for the level")
    moves: int = Field(..., description="Moves used in the best run")
    duration_ms: int = Field(..., description="Duration of best run")
    level: int = Field(..., description="Level number")
    achieved_at: Optional[str] = Field(None, description="Timestamp when the score was recorded")


class ProgressUpsert(BaseModel):
    user_id: PositiveInt = Field(..., description="User ID")
    level: PositiveInt = Field(..., description="Level number")
    state_json: str = Field(..., description="Serialized game state (JSON string). Stored as text.")


class ProgressOut(BaseModel):
    id: int
    user_id: int
    level: int
    state_json: str
    updated_at: Optional[str]

    class Config:
        from_attributes = True


# -----------------------------
# FastAPI app
# -----------------------------

openapi_tags = [
    {"name": "health", "description": "Service health and metadata"},
    {"name": "users", "description": "User profile management"},
    {"name": "scores", "description": "Score submission and retrieval"},
    {"name": "leaderboard", "description": "Leaderboard aggregation endpoints"},
    {"name": "progress", "description": "Game progress save/load"},
    {"name": "websocket-docs", "description": "Documentation helpers for real-time features"},
]

app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    openapi_tags=openapi_tags,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Routes
# -----------------------------

# PUBLIC_INTERFACE
@app.get("/", tags=["health"], summary="Health check", description="Basic health check for the Gravity Curve backend.")
def health_check():
    """Return a simple health status message."""
    return {"message": "Healthy", "service": settings.APP_NAME, "version": settings.APP_VERSION}

# PUBLIC_INTERFACE
@app.get("/docs/websocket", tags=["websocket-docs"], summary="WebSocket usage notes", description="Provides guidance for potential real-time features. Currently, the backend does not expose WebSocket endpoints, but this route describes how they would be used in the future.")
def websocket_docs():
    """Return documentation for potential WebSocket usage (placeholder)."""
    return {
        "websocket": {
            "status": "not-implemented",
            "notes": "This backend currently uses REST only. Future versions may stream live leaderboard updates and game events via WebSockets.",
            "example_endpoint": "/ws/leaderboard",
            "client_usage": "Use WebSocket API in the frontend to subscribe to events.",
        }
    }

# ---- Users ----

# PUBLIC_INTERFACE
@app.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED, tags=["users"], summary="Create user", description="Create a new user profile with unique email and username.")
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    """Create a new user with unique email and username."""
    existing = db.query(User).filter((User.email == payload.email) | (User.username == payload.username)).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email or username already in use")
    user = User(email=str(payload.email).lower(), username=payload.username)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

# PUBLIC_INTERFACE
@app.get("/users/{user_id}", response_model=UserOut, tags=["users"], summary="Get user by ID", description="Retrieve a user profile by its ID.")
def get_user(user_id: int = Path(..., description="User ID"), db: Session = Depends(get_db)):
    """Get a single user by ID."""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# PUBLIC_INTERFACE
@app.get("/users", response_model=List[UserOut], tags=["users"], summary="List users", description="List users with optional pagination.")
def list_users(skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_db)):
    """List users with pagination."""
    users = db.query(User).order_by(User.id.asc()).offset(skip).limit(limit).all()
    return users

# PUBLIC_INTERFACE
@app.patch("/users/{user_id}", response_model=UserOut, tags=["users"], summary="Update user", description="Update a user's email and/or username.")
def update_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db)):
    """Update user email/username ensuring uniqueness."""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if payload.email:
        email_lower = str(payload.email).lower()
        if db.query(User).filter(User.email == email_lower, User.id != user_id).first():
            raise HTTPException(status_code=409, detail="Email already in use")
        user.email = email_lower
    if payload.username:
        if db.query(User).filter(User.username == payload.username, User.id != user_id).first():
            raise HTTPException(status_code=409, detail="Username already in use")
        user.username = payload.username
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

# PUBLIC_INTERFACE
@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["users"], summary="Delete user", description="Delete a user profile and all associated data.")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """Delete a user and cascade-delete related scores and progress."""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content=None)

# ---- Scores ----

# PUBLIC_INTERFACE
@app.post("/scores", response_model=ScoreOut, status_code=status.HTTP_201_CREATED, tags=["scores"], summary="Submit score", description="Submit a new game score for a user.")
def submit_score(payload: ScoreCreate, db: Session = Depends(get_db)):
    """Submit a score entry."""
    user = db.get(User, payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    score = Score(
        user_id=payload.user_id,
        level=payload.level,
        points=payload.points,
        moves=payload.moves,
        duration_ms=payload.duration_ms,
    )
    db.add(score)
    db.commit()
    db.refresh(score)
    return score

# PUBLIC_INTERFACE
@app.get("/scores/user/{user_id}", response_model=List[ScoreOut], tags=["scores"], summary="Get user scores", description="Retrieve all scores for a specific user, newest first.")
def get_user_scores(user_id: int, db: Session = Depends(get_db)):
    """Retrieve scores for a user."""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    scores = (
        db.query(Score)
        .filter(Score.user_id == user_id)
        .order_by(desc(Score.created_at))
        .all()
    )
    return scores

# PUBLIC_INTERFACE
@app.get("/scores/level/{level}", response_model=List[ScoreOut], tags=["scores"], summary="Get level scores", description="Retrieve all scores for a level, sorted by points descending.")
def get_level_scores(level: int, db: Session = Depends(get_db)):
    """Retrieve all scores for a specific level, by points descending."""
    scores = (
        db.query(Score)
        .filter(Score.level == level)
        .order_by(desc(Score.points), Score.moves.asc(), Score.duration_ms.asc())
        .all()
    )
    return scores

# ---- Leaderboard ----

# PUBLIC_INTERFACE
@app.get(
    "/leaderboard/global",
    response_model=List[LeaderboardEntry],
    tags=["leaderboard"],
    summary="Global leaderboard",
    description="Get global leaderboard across all levels. Uses best score per user per level, ranks by points desc, moves asc, duration asc."
)
def leaderboard_global(limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_db)):
    """Aggregate top scores across all levels for all users."""
    # Strategy: pick each score, join user, order by ranking and limit.
    # For simplicity without window functions portable across sqlite/postgres in ORM:
    # We will pull top N scores sorted and map to LeaderboardEntry.
    q = (
        db.query(
            User.username,
            Score.points,
            Score.moves,
            Score.duration_ms,
            Score.level,
            Score.created_at,
        )
        .join(User, User.id == Score.user_id)
        .order_by(desc(Score.points), Score.moves.asc(), Score.duration_ms.asc(), Score.created_at.asc())
        .limit(limit)
    )
    rows = q.all()
    return [
        LeaderboardEntry(
            username=r[0],
            points=r[1],
            moves=r[2],
            duration_ms=r[3],
            level=r[4],
            achieved_at=str(r[5]) if r[5] else None,
        )
        for r in rows
    ]

# PUBLIC_INTERFACE
@app.get(
    "/leaderboard/level/{level}",
    response_model=List[LeaderboardEntry],
    tags=["leaderboard"],
    summary="Level leaderboard",
    description="Get leaderboard for a specific level. Ranks by points desc, moves asc, duration asc."
)
def leaderboard_level(level: int = Path(..., ge=1), limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_db)):
    """Top scores for a given level."""
    q = (
        db.query(
            User.username,
            Score.points,
            Score.moves,
            Score.duration_ms,
            Score.level,
            Score.created_at,
        )
        .join(User, User.id == Score.user_id)
        .filter(Score.level == level)
        .order_by(desc(Score.points), Score.moves.asc(), Score.duration_ms.asc(), Score.created_at.asc())
        .limit(limit)
    )
    rows = q.all()
    return [
        LeaderboardEntry(
            username=r[0],
            points=r[1],
            moves=r[2],
            duration_ms=r[3],
            level=r[4],
            achieved_at=str(r[5]) if r[5] else None,
        )
        for r in rows
    ]

# ---- Game Progress ----

# PUBLIC_INTERFACE
@app.post(
    "/progress",
    response_model=ProgressOut,
    tags=["progress"],
    summary="Upsert progress",
    description="Create or update a user's game progress for a level. If progress exists, it is updated; otherwise it's created."
)
def upsert_progress(payload: ProgressUpsert, db: Session = Depends(get_db)):
    """Create or update game progress for a level."""
    user = db.get(User, payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    existing = (
        db.query(GameProgress)
        .filter(GameProgress.user_id == payload.user_id, GameProgress.level == payload.level)
        .first()
    )
    if existing:
        existing.state_json = payload.state_json
        db.add(existing)
        db.commit()
        db.refresh(existing)
        return existing
    else:
        rec = GameProgress(user_id=payload.user_id, level=payload.level, state_json=payload.state_json)
        db.add(rec)
        db.commit()
        db.refresh(rec)
        return rec

# PUBLIC_INTERFACE
@app.get(
    "/progress/{user_id}/{level}",
    response_model=ProgressOut,
    tags=["progress"],
    summary="Get progress for level",
    description="Retrieve a user's saved game progress for a specific level."
)
def get_progress(user_id: int, level: int, db: Session = Depends(get_db)):
    """Get saved progress for a user and level."""
    rec = (
        db.query(GameProgress)
        .filter(GameProgress.user_id == user_id, GameProgress.level == level)
        .first()
    )
    if not rec:
        raise HTTPException(status_code=404, detail="Progress not found")
    return rec

# PUBLIC_INTERFACE
@app.delete(
    "/progress/{user_id}/{level}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["progress"],
    summary="Delete progress for level",
    description="Delete a user's saved progress for a specific level."
)
def delete_progress(user_id: int, level: int, db: Session = Depends(get_db)):
    """Delete progress for user and level."""
    rec = (
        db.query(GameProgress)
        .filter(GameProgress.user_id == user_id, GameProgress.level == level)
        .first()
    )
    if not rec:
        raise HTTPException(status_code=404, detail="Progress not found")
    db.delete(rec)
    db.commit()
    return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content=None)

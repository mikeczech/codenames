from typing import Optional, List
from fastapi import FastAPI, Depends, Cookie, Request, HTTPException, Form
from sqlalchemy.orm import Session

from codenames import models, schemas
from codenames.sql import SQLAlchemyGameManager, SQLAlchemyGameBackend
from codenames.game import (
    Game,
    Color,
    Role,
    RoleOccupiedException,
    AlreadyJoinedException,
)
from codenames.database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()


def get_game_manager():
    db = SessionLocal()
    manager = SQLAlchemyGameManager(db)
    try:
        yield manager
    finally:
        db.close()


def get_game_backend(game_id: int):
    db = SessionLocal()
    backend = SQLAlchemyGameBackend(game_id, db)
    try:
        yield backend
    finally:
        db.close()


@app.get("/games/{game_id}/words")
def read_active_words(backend: SQLAlchemyGameBackend = Depends(get_game_backend)):
    return [
        {"color": w.color, "word": w.word.value} for w in backend.read_active_words()
    ]


@app.get("/games/{game_id}/hints", response_model=List[schemas.Hint])
def read_hints(backend: SQLAlchemyGameBackend = Depends(get_game_backend)):
    return backend.read_hints()


@app.get("/games/{game_id}/players", response_model=List[schemas.Player])
def read_players(backend: SQLAlchemyGameBackend = Depends(get_game_backend)):
    return backend.read_players()


@app.get("/games/{game_id}/conditions", response_model=List[schemas.Condition])
def read_conditions(backend: SQLAlchemyGameBackend = Depends(get_game_backend)):
    return backend.read_conditions()


@app.post("/games/{game_id}/join")
def join_game(
    color_id: int = Form(...),
    role_id: int = Form(...),
    session_id: Optional[str] = Cookie(None),
    backend: SQLAlchemyGameBackend = Depends(get_game_backend),
):
    if session_id is None:
        raise HTTPException(status_code=401, detail="Could not determine session id")
    current_game_state = Game(session_id, backend).load_state()
    try:
        current_game_state.join(Color(color_id), Role(role_id))
    except RoleOccupiedException:
        raise HTTPException(
            status_code=403,
            detail="The given color/role is already occupied by another player",
        )
    except AlreadyJoinedException:
        raise HTTPException(
            status_code=403, detail="It seems you already joined the game"
        )
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Cannot join the game (maybe the game is already running)",
        )
    return backend.read_conditions()


@app.post("/games/")
def create_game(
    name: str = Form(...),
    session_id: Optional[str] = Cookie(None),
    game_manager: SQLAlchemyGameManager = Depends(get_game_manager),
):
    game_manager.create_random(name, session_id)
    return "hello"

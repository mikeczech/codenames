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
    GameAlreadyExistsException,
    AuthorizationException,
    InvalidColorRoleCombination,
    StateException,
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
        {
            "color": w.color,
            "word": w.word.value,
            "id": w.id,
            "is_active": False if w.move else True,
        }
        for w in backend.read_active_words()
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


@app.put("/games/{game_id}/join")
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
    except RoleOccupiedException as ex:
        raise HTTPException(
            status_code=403,
            detail="This color and role is already occupied by another player",
        )
    except AlreadyJoinedException as ex:
        raise HTTPException(
            status_code=403, detail="This user has already joined the game"
        )
    except InvalidColorRoleCombination as ex:
        raise HTTPException(
            status_code=403,
            detail=f"Invalid color / role combination: color = {color_id}, role = {role_id}",
        )
    except StateException as ex:
        raise HTTPException(
            status_code=400,
            detail=ex.message,
        )
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Cannot join the game (maybe the game is already running)",
        )
    return {
        "message": f"Successfully joined the game {backend.game_id} with color {color_id} and role {role_id}."
    }


@app.put("/games/{game_id}/start")
def start_game(
    session_id: Optional[str] = Cookie(None),
    backend: SQLAlchemyGameBackend = Depends(get_game_backend),
):
    if session_id is None:
        raise HTTPException(status_code=401, detail="Could not determine session id")
    current_game_state = Game(session_id, backend).load_state()
    try:
        current_game_state.start_game()
    except StateException as ex:
        raise HTTPException(status_code=403, detail=ex.message)
    except Exception as ex:
        raise HTTPException(status_code=400, detail="Cannot start the game")

    return {"message": "Successfully started the game"}


@app.put("/games/{game_id}/give_hint")
def give_hint(
    word: str = Form(...),
    num: int = Form(...),
    session_id: Optional[str] = Cookie(None),
    backend: SQLAlchemyGameBackend = Depends(get_game_backend),
):
    if session_id is None:
        raise HTTPException(status_code=401, detail="Could not determine session id")
    current_game_state = Game(session_id, backend).load_state()
    try:
        current_game_state.give_hint(word, num)
    except AuthorizationException as ex:
        raise HTTPException(status_code=401, detail=ex.message)
    except StateException as ex:
        raise HTTPException(status_code=403, detail=ex.message)
    except Exception as ex:
        raise HTTPException(status_code=400, detail="Cannot give a hint")

    return {"message": f"Successfully given the hint '{word}' with num = {num}"}


@app.put("/games/{game_id}/end_turn")
def end_turn(
    session_id: Optional[str] = Cookie(None),
    backend: SQLAlchemyGameBackend = Depends(get_game_backend),
):
    if session_id is None:
        raise HTTPException(status_code=401, detail="Could not determine session id")
    current_game_state = Game(session_id, backend).load_state()
    try:
        current_game_state.end_turn()
    except AuthorizationException as ex:
        raise HTTPException(status_code=401, detail=ex.message)
    except StateException as ex:
        raise HTTPException(status_code=403, detail=ex.message)
    except Exception as ex:
        raise HTTPException(status_code=400, detail="Cannot end turn")

    return {"message": f"Successfully ended the turn"}


@app.put("/games/{game_id}/guess")
def guess(
    word_id: int = Form(...),
    session_id: Optional[str] = Cookie(None),
    backend: SQLAlchemyGameBackend = Depends(get_game_backend),
):
    if session_id is None:
        raise HTTPException(status_code=401, detail="Could not determine session id")
    current_game_state = Game(session_id, backend).load_state()
    try:
        current_game_state.guess(word_id)
    except AuthorizationException as ex:
        raise HTTPException(status_code=401, detail=ex.message)
    except StateException as ex:
        raise HTTPException(status_code=403, detail=ex.message)
    except Exception as ex:
        raise HTTPException(status_code=400, detail="Cannot give a hint")

    return {"message": f"Successfully guessed word '{word_id}'"}


@app.post("/games/")
def create_game(
    name: str = Form(...),
    session_id: Optional[str] = Cookie(None),
    game_manager: SQLAlchemyGameManager = Depends(get_game_manager),
):
    try:
        game = game_manager.create_random(name, session_id, random_seed=42)
    except GameAlreadyExistsException as ex:
        raise HTTPException(status_code=403, detail=f"The game {name} already exists")
    except Exception as ex:
        raise HTTPException(status_code=400, detail="Could not create the game")

    return {
        "message": f"Successfully created the game '{name}'.",
        "game_id": game.id,
    }

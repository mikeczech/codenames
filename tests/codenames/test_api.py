from codenames.api import app, get_game_manager, get_game_backend
from codenames.models import Base
from codenames.sql import SQLAlchemyGameManager, SQLAlchemyGameBackend
from codenames.game import Color, Role, Condition

import alembic
from alembic.config import Config
from pytest import fixture
from fastapi.testclient import TestClient

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///instance/test.sqlite"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

alembic_cfg = Config("alembic.ini")
alembic_cfg.set_main_option("sqlalchemy.url", SQLALCHEMY_DATABASE_URL)


def get_test_game_manager():
    db = TestingSessionLocal()
    manager = SQLAlchemyGameManager(db)
    try:
        yield manager
    finally:
        db.close()


def get_test_game_backend(game_id: int):
    db = TestingSessionLocal()
    backend = SQLAlchemyGameBackend(game_id, db)
    try:
        yield backend
    finally:
        db.close()


app.dependency_overrides[get_game_manager] = get_test_game_manager
app.dependency_overrides[get_game_backend] = get_test_game_backend


@fixture
def client():
    return TestClient(app)


@fixture
def test_db():
    alembic.command.upgrade(alembic_cfg, "head")
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_game_api(client, test_db):
    # create random game
    response = client.post("/games/", json={"name": "testgame"})
    assert response.status_code == 200, response.text
    game_id = response.json()["game_id"]

    response = client.get(f"/games/{game_id}/words")
    assert response.status_code == 200, response.text
    assert len(response.json()) == 28

    response = client.get(f"/games/{game_id}/hints")
    assert response.status_code == 200, response.text
    assert len(response.json()) == 1

    response = client.get(f"/games/{game_id}/conditions")
    assert response.status_code == 200, response.text
    assert len(response.json()) == 1

    # add players
    for player_id, color, role in [
        ("p1", Color.RED, Role.PLAYER),
        ("p2", Color.RED, Role.SPYMASTER),
        ("p3", Color.BLUE, Role.PLAYER),
        ("p4", Color.BLUE, Role.SPYMASTER),
    ]:
        response = client.put(
            f"/games/{game_id}/join",
            json={"color_id": color.value, "role_id": role.value},
            headers={"Cookie": f"session_id={player_id}"},
        )
        assert response.status_code == 200, response.text

    response = client.put(
        f"/games/{game_id}/start", headers={"Cookie": f"session_id=p1"}
    )
    assert response.status_code == 200, response.text

    # blue spymaster gives a hint
    response = client.put(
        f"/games/{game_id}/give_hint",
        json={"word": "myhint", "num": 2},
        headers={"Cookie": f"session_id=p4"},
    )
    assert response.status_code == 200, response.text

    response = client.get(f"/games/{game_id}/hints")
    assert response.status_code == 200, response.text
    assert len(response.json()) == 2

    # three correct guesses
    for word_id in [21, 17, 22]:
        response = client.put(
            f"/games/{game_id}/guess",
            json={"word_id": word_id},
            headers={"Cookie": f"session_id=p3"},
        )
        assert response.status_code == 200, f"'{response.text}', {word_id}"

    # red spymaster gives a hint
    response = client.put(
        f"/games/{game_id}/give_hint",
        json={"word": "nexthint", "num": 5},
        headers={"Cookie": f"session_id=p2"},
    )
    assert response.status_code == 200, response.text

    response = client.get(f"/games/{game_id}/hints")
    assert response.status_code == 200, response.text
    assert len(response.json()) == 3

    # one guess and then end turn
    response = client.put(
        f"/games/{game_id}/guess",
        json={"word_id": 1},
        headers={"Cookie": f"session_id=p1"},
    )
    assert response.status_code == 200, response.text

    response = client.put(
        f"/games/{game_id}/end_turn", headers={"Cookie": f"session_id=p1"}
    )
    assert response.status_code == 200, response.text

    # blue spymaster gives a hint
    response = client.put(
        f"/games/{game_id}/give_hint",
        json={"word": "nexthint", "num": 5},
        headers={"Cookie": f"session_id=p4"},
    )
    assert response.status_code == 200, response.text

    response = client.get(f"/games/{game_id}/hints")
    assert response.status_code == 200, response.text
    assert len(response.json()) == 4

    # wrong guess
    response = client.put(
        f"/games/{game_id}/guess",
        json={"word_id": 10},
        headers={"Cookie": f"session_id=p3"},
    )
    assert response.status_code == 200, response.text

    # red spymaster gives a hint
    response = client.put(
        f"/games/{game_id}/give_hint",
        json={"word": "anotherhint", "num": 4},
        headers={"Cookie": f"session_id=p2"},
    )
    assert response.status_code == 200, response.text

    response = client.get(f"/games/{game_id}/hints")
    assert response.status_code == 200, response.text
    assert len(response.json()) == 5

    # guess of assassin ends game and blue wins
    response = client.put(
        f"/games/{game_id}/guess",
        json={"word_id": 8},
        headers={"Cookie": f"session_id=p1"},
    )
    assert response.status_code == 200, response.text

    response = client.get(f"/games/{game_id}/conditions")
    assert response.status_code == 200, response.text
    assert len(response.json()) == 13
    assert response.json()[-1]["condition"] == Condition.BLUE_WINS.value

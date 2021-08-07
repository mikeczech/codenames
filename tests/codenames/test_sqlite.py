import pytest

from codenames.game import (
    Word,
    Color,
    Role,
    Condition,
    GameAlreadyExistsException,
    StateException,
)
from codenames.sqlite import SQLiteGameManager, SQLiteGameBackend

from utils import create_default_game, add_players


class TestSQLiteGameBackend:
    def test_load(self, db_con):
        # given
        backend = SQLiteGameBackend(42, db_con)
        create_default_game(db_con)

        # when
        result = backend.load()

        # then
        assert result == {
            "words": {
                1: Word(id=1, value="Hollywood", color=Color.RED, selected_at=None),
                2: Word(id=2, value="Well", color=Color.BLUE, selected_at=None),
                3: Word(id=3, value="Foot", color=Color.RED, selected_at=None),
                4: Word(id=4, value="New York", color=Color.BLUE, selected_at=None),
                5: Word(id=5, value="Spring", color=Color.NEUTRAL, selected_at=None),
                6: Word(id=6, value="Court", color=Color.ASSASSIN, selected_at=None),
                7: Word(id=7, value="Tube", color=Color.BLUE, selected_at=None),
                8: Word(id=8, value="Point", color=Color.RED, selected_at=None),
            },
            "hints": [{"id": 1, "word": None, "num": None, "color": None}],
            "conditions": [{"hint_id": None, "value": Condition.NOT_STARTED}],
            "players": [],
        }

    def test_guess_word(self, db_con):
        # given
        backend = SQLiteGameBackend(42, db_con)
        create_default_game(db_con)

        # when
        backend.add_guess(1)

        # then
        result = backend.load()
        assert result["words"][1].selected_at
        assert not result["words"][2].selected_at

    def test_add_hints(self, db_con):
        # given
        backend = SQLiteGameBackend(42, db_con)
        create_default_game(db_con)

        # when
        backend.add_hint("myfirsthint", 2, Color.RED)
        backend.add_hint("mysecondhint", 3, Color.BLUE)

        # then
        result = backend.load()["hints"]
        assert result[1]["word"] == "myfirsthint"
        assert result[1]["num"] == 2
        assert result[1]["color"] == Color.RED
        assert result[2]["word"] == "mysecondhint"
        assert result[2]["num"] == 3
        assert result[2]["color"] == Color.BLUE

    def test_add_condition(self, db_con):
        # given
        backend = SQLiteGameBackend(42, db_con)
        create_default_game(db_con)
        add_players(db_con)

        # when
        backend.add_condition(Condition.BLUE_SPY)

        # then
        assert backend.load()["conditions"][-1]["value"] == Condition.BLUE_SPY

    def test_has_joined(self, db_con):
        # given
        backend = SQLiteGameBackend(42, db_con)
        create_default_game(db_con)
        add_players(db_con)  # adds session id A23 but not A34

        # when
        has_joined = backend.has_joined("A23")
        has_not_joined = backend.has_joined("A34")

        # then
        assert has_joined
        assert not has_not_joined

    def test_add_players(self, db_con):
        # given
        backend = SQLiteGameBackend(42, db_con)
        create_default_game(db_con)

        # when
        backend.add_player("ABDB23", Color.RED, Role.PLAYER)
        backend.add_player("ABDB55", Color.BLUE, Role.PLAYER)
        backend.add_player("ABDB33", Color.RED, Role.SPYMASTER)
        backend.add_player("ABDB67", Color.BLUE, Role.SPYMASTER)

        # then
        result = backend.load()["players"]
        assert result[0] == {
            "session_id": "ABDB23",
            "color": Color.RED,
            "role": Role.PLAYER,
        }
        assert result[1] == {
            "session_id": "ABDB55",
            "color": Color.BLUE,
            "role": Role.PLAYER,
        }
        assert result[2] == {
            "session_id": "ABDB33",
            "color": Color.RED,
            "role": Role.SPYMASTER,
        }
        assert result[3] == {
            "session_id": "ABDB67",
            "color": Color.BLUE,
            "role": Role.SPYMASTER,
        }

    def test_remove_players(self, db_con):
        # given
        backend = SQLiteGameBackend(42, db_con)
        create_default_game(db_con)
        add_players(db_con)

        # when
        backend.remove_player("A100")

        # then
        result = backend.load()["players"]
        assert len(result) == 3
        assert "A100" not in [r["session_id"] for r in result]


class TestSQLiteGameManager:
    def test_create_random_game(self, db_con):
        # given
        manager = SQLiteGameManager(db_con, num_blue=2, num_red=2, num_neutral=2)

        # when
        game = manager.create_random("my_game", "mysessionid")

        # then
        assert game.id == 1

    def test_random_game_state_is_valid(self, db_con):
        # given
        manager = SQLiteGameManager(db_con, num_blue=2, num_red=2, num_neutral=2)

        # when
        info = manager.create_random("my_game", "mysessionid").load_state().get_info()

        # then
        assert len(info["words"]) == 7
        assert info["conditions"][-1]["value"] == Condition.NOT_STARTED

    def test_initially_there_is_no_game(self, db_con):
        # given
        manager = SQLiteGameManager(db_con, num_blue=2, num_red=2, num_neutral=2)

        # when
        result = manager.exists("my_game")

        # then
        assert not result

    def test_a_created_game_exists(self, db_con):
        # given
        manager = SQLiteGameManager(db_con, num_blue=2, num_red=2, num_neutral=2)
        manager.create_random("my_game", "mysessionid")

        # when
        result = manager.exists("my_game")

        # then
        assert result

    def test_creating_duplicates_fails(self, db_con):
        # given
        manager = SQLiteGameManager(db_con, num_blue=2, num_red=2, num_neutral=2)

        # when
        manager.create_random("my_game", "mysessionid")

        # then
        with pytest.raises(GameAlreadyExistsException):
            manager.create_random("my_game", "mysessionid")

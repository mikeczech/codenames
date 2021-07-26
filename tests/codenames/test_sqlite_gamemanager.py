import pytest

from codenames.game import (
    SQLiteGameManager,
    SQLiteGamePersister,
    Word,
    Color,
    Role,
    Condition,
    GameAlreadyExistsException,
    StateException,
)

from utils import create_default_game, add_players


class TestSQLiteGamePersister:
    def test_load(self, db_con):
        # given
        persister = SQLiteGamePersister(42, db_con)
        create_default_game(db_con)

        # when
        result = persister.load()

        # then
        assert result == {
            "words": [
                Word(id=1, value="Hollywood", color=Color.RED, selected_at=None),
                Word(id=2, value="Well", color=Color.BLUE, selected_at=None),
                Word(id=3, value="Foot", color=Color.RED, selected_at=None),
                Word(id=4, value="New York", color=Color.BLUE, selected_at=None),
                Word(id=5, value="Spring", color=Color.NEUTRAL, selected_at=None),
                Word(id=6, value="Court", color=Color.ASSASSIN, selected_at=None),
                Word(id=7, value="Tube", color=Color.BLUE, selected_at=None),
                Word(id=8, value="Point", color=Color.RED, selected_at=None),
            ],
            "hints": [{"id": 1, "word": None, "num": None, "color": None}],
            "turns": [{"hint_id": None, "condition": Condition.NOT_STARTED}],
            "players": [],
            "metadata": {"condition": Condition.NOT_STARTED},
        }

    def test_guess_word(self, db_con):
        # given
        persister = SQLiteGamePersister(42, db_con)
        create_default_game(db_con)

        # when
        persister.add_guess(1)

        # then
        result = persister.load()
        assert result["words"][0].selected_at
        assert not result["words"][1].selected_at

    def test_add_hints(self, db_con):
        # given
        persister = SQLiteGamePersister(42, db_con)
        create_default_game(db_con)

        # when
        persister.add_hint("myfirsthint", 2, Color.RED)
        persister.add_hint("mysecondhint", 3, Color.BLUE)

        # then
        result = persister.load()["hints"]
        assert result[1]["word"] == "myfirsthint"
        assert result[1]["num"] == 2
        assert result[1]["color"] == Color.RED
        assert result[2]["word"] == "mysecondhint"
        assert result[2]["num"] == 3
        assert result[2]["color"] == Color.BLUE

    def test_push_condition(self, db_con):
        # given
        persister = SQLiteGamePersister(42, db_con)
        create_default_game(db_con)
        add_players(db_con)

        # when
        persister.push_condition(Condition.BLUE_SPY)

        # then
        metadata = persister.load()["metadata"]
        assert metadata["condition"] == Condition.BLUE_SPY

    def test_has_joined(self, db_con):
        # given
        persister = SQLiteGamePersister(42, db_con)
        create_default_game(db_con)
        add_players(db_con)  # adds session id A23 but not A34

        # when
        has_joined = persister.has_joined("A23")
        has_not_joined = persister.has_joined("A34")

        # then
        assert has_joined
        assert not has_not_joined

    def test_add_players(self, db_con):
        # given
        persister = SQLiteGamePersister(42, db_con)
        create_default_game(db_con)

        # when
        persister.add_player("ABDB23", False, Color.RED, Role.PLAYER)
        persister.add_player("ABDB55", False, Color.BLUE, Role.PLAYER)
        persister.add_player("ABDB33", True, Color.RED, Role.SPYMASTER)
        persister.add_player("ABDB67", False, Color.BLUE, Role.SPYMASTER)

        # then
        result = persister.load()["players"]
        assert result[0] == {
            "session_id": "ABDB23",
            "color": Color.RED,
            "role": Role.PLAYER,
            "is_admin": False,
        }
        assert result[1] == {
            "session_id": "ABDB55",
            "color": Color.BLUE,
            "role": Role.PLAYER,
            "is_admin": False,
        }
        assert result[2] == {
            "session_id": "ABDB33",
            "color": Color.RED,
            "role": Role.SPYMASTER,
            "is_admin": True,
        }
        assert result[3] == {
            "session_id": "ABDB67",
            "color": Color.BLUE,
            "role": Role.SPYMASTER,
            "is_admin": False,
        }

    def test_remove_players(self, db_con):
        # given
        persister = SQLiteGamePersister(42, db_con)
        create_default_game(db_con)
        add_players(db_con)

        # when
        persister.remove_player("A100")

        # then
        result = persister.load()["players"]
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
        assert info["metadata"]["condition"] == Condition.NOT_STARTED

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

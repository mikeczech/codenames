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
            ],
            "hints": [],
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
        assert result[0]["word"] == "myfirsthint"
        assert result[0]["num"] == 2
        assert result[0]["color"] == Color.RED
        assert result[1]["word"] == "mysecondhint"
        assert result[1]["num"] == 3
        assert result[1]["color"] == Color.BLUE

    def test_start_game(self, db_con):
        # given
        persister = SQLiteGamePersister(42, db_con)
        create_default_game(db_con)
        add_players(db_con)

        # when
        persister.start_game()

        # then
        metadata = persister.load()["metadata"]
        assert metadata["condition"] == Condition.BLUE_SPY

    def test_start_not_ready_game(self, db_con):
        # given
        persister = SQLiteGamePersister(42, db_con)
        create_default_game(db_con)

        # when / then
        with pytest.raises(StateException):
            persister.start_game()

    def test_starting_a_game_twice_fails(self, db_con):
        # given
        persister = SQLiteGamePersister(42, db_con)
        create_default_game(db_con)
        add_players(db_con)

        # when / then
        with pytest.raises(StateException):
            persister.start_game()
            persister.start_game()

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

    def test_adding_same_role_twice_fails(self, db_con):
        # given
        persister = SQLiteGamePersister(42, db_con)
        create_default_game(db_con)

        # when / then
        with pytest.raises(StateException):
            persister.add_player("ABDB23", False, Color.RED, Role.PLAYER)
            persister.add_player("ABDB23", False, Color.RED, Role.PLAYER)

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

    def test_removing_not_existing_player_fails(self, db_con):
        # given
        persister = SQLiteGamePersister(42, db_con)
        create_default_game(db_con)
        add_players(db_con)

        # when / then
        with pytest.raises(StateException):
            persister.remove_player("A222")


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

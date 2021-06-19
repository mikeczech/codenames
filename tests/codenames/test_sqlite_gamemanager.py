import os
import csv
import sqlite3

import pytest

from codenames.game import (
    SQLiteGameManager,
    Hint,
    SQLiteGameState,
    Color,
    Role,
    Condition,
    GameAlreadyExistsException,
    StateException,
)


@pytest.fixture
def db_con():
    con = sqlite3.connect(":memory:")
    cursor = con.cursor()

    this_dir, _ = os.path.split(__file__)
    schema_path = os.path.join(this_dir, "..", "..", "codenames", "schema.sql")
    words_path = os.path.join(this_dir, "..", "..", "codenames", "data", "words.csv")

    with open(schema_path, "r") as f:
        cursor.executescript(f.read())

    with open(words_path, "r") as f:
        rows = csv.DictReader(f)
        to_db = [(r["id"], r["word"]) for r in rows]

    cursor.executemany("INSERT INTO words (id, value) VALUES (?, ?);", to_db)

    return con


class TestSQLiteGameState:
    def _create_default_game(self, db_con):
        """ Adds a simple game to the database. """
        active_words = [(42, 1, Color.RED.value), (42, 2, Color.BLUE.value)]
        turns = [(42, Condition.NOT_STARTED.value)]
        db_con.executemany(
            """
            INSERT INTO active_words (game_id, word_id, color) VALUES (?, ?, ?)
        """,
            active_words,
        )
        db_con.executemany(
            """
            INSERT INTO turns (game_id, condition, created_at) VALUES (?, ?, strftime('%s', 'now'))
        """,
            turns,
        )

    def _add_players(self, db_con):
        players = [
                (42, 23, Color.RED.value, Role.PLAYER.value, False),
                (42, 22, Color.BLUE.value, Role.SPYMASTER.value, True),
                (42, 21, Color.RED.value, Role.PLAYER.value, False),
                (42, 20, Color.BLUE.value, Role.SPYMASTER.value, False),
        ]
        db_con.executemany(
            """
            INSERT INTO players (game_id, session_id, color, role, is_admin) VALUES (?, ?, ?, ?, ?)
        """,
            players,
        )

    def test_load(self, db_con):
        # given
        state = SQLiteGameState(42, db_con)
        self._create_default_game(db_con)

        # when
        result = state.load()

        # then
        assert result == {
            "words": [
                {
                    "id": 1,
                    "value": "Hollywood",
                    "color": Color.RED,
                    "selected_at": None,
                },
                {"id": 2, "value": "Well", "color": Color.BLUE, "selected_at": None},
            ],
            "hints": [],
            "metadata": {"condition": Condition.NOT_STARTED},
        }

    def test_guess_word(self, db_con):
        # given
        state = SQLiteGameState(42, db_con)
        self._create_default_game(db_con)

        # when
        state.guess(1)

        # then
        result = state.load()
        assert result["words"][0]["selected_at"]
        assert not result["words"][1]["selected_at"]

    def test_add_hints(self, db_con):
        # given
        state = SQLiteGameState(42, db_con)
        self._create_default_game(db_con)

        # when
        state.add_hint("myfirsthint", 2, Color.RED)
        state.add_hint("mysecondhint", 3, Color.BLUE)

        # then
        result = state.load()["hints"]
        assert result[0]["word"] == "myfirsthint"
        assert result[0]["num"] == 2
        assert result[0]["color"] == Color.RED
        assert result[1]["word"] == "mysecondhint"
        assert result[1]["num"] == 3
        assert result[1]["color"] == Color.BLUE

    def test_start_game(self, db_con):
        # given
        state = SQLiteGameState(42, db_con)
        self._create_default_game(db_con)
        self._add_players(db_con)

        # when
        state.start_game()

        # then
        metadata = state.load()["metadata"]
        assert metadata["condition"] == Condition.BLUE_SPY

    def test_start_not_ready_game(self, db_con):
        # given
        state = SQLiteGameState(42, db_con)
        self._create_default_game(db_con)

        # when / then
        with pytest.raises(StateException):
            state.start_game()

    def test_starting_a_game_twice_fails(self, db_con):
        # given
        state = SQLiteGameState(42, db_con)
        self._create_default_game(db_con)
        self._add_players(db_con)

        # when / then
        with pytest.raises(StateException):
            state.start_game()
            state.start_game()


class TestSQLiteGameManager:
    def test_create_random_game(self, db_con):
        # given
        manager = SQLiteGameManager(db_con, num_blue=2, num_red=2, num_neutral=2)

        # when
        game = manager.create_random("my_game")

        # then
        assert game.id == 1

    def test_random_game_state_is_valid(self, db_con):
        # given
        manager = SQLiteGameManager(db_con, num_blue=2, num_red=2, num_neutral=2)

        # when
        state = manager.create_random("my_game").get_state()

        # then
        assert len(state["words"]) == 7
        assert state["metadata"]["condition"] == Condition.NOT_STARTED

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
        manager.create_random("my_game")

        # when
        result = manager.exists("my_game")

        # then
        assert result

    def test_creating_duplicates_fails(self, db_con):
        # given
        manager = SQLiteGameManager(db_con, num_blue=2, num_red=2, num_neutral=2)

        # when
        manager.create_random("my_game")

        # then
        with pytest.raises(GameAlreadyExistsException):
            manager.create_random("my_game")

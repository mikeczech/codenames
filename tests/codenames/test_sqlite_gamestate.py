import os
import csv
import sqlite3

import pytest

from codenames.game import SQLiteGameManager, Condition, GameAlreadyExistsException


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


def test_create_random_game(db_con):
    # given
    manager = SQLiteGameManager(db_con, num_blue=2, num_red=2, num_neutral=2)

    # when
    game = manager.create_random("my_game")

    # then
    assert game.id == 1


def test_random_game_state_is_valid(db_con):
    # given
    manager = SQLiteGameManager(db_con, num_blue=2, num_red=2, num_neutral=2)

    # when
    state = manager.create_random("my_game").get_state()

    # then
    assert len(state["words"]) == 7
    assert state["metadata"]["condition"] == Condition.NOT_STARTED

def test_initially_there_is_no_game(db_con):
    # given
    manager = SQLiteGameManager(db_con, num_blue=2, num_red=2, num_neutral=2)

    # when
    result = manager.exists("my_game")

    # then
    assert not result

def test_a_created_game_exists(db_con):
    # given
    manager = SQLiteGameManager(db_con, num_blue=2, num_red=2, num_neutral=2)
    manager.create_random("my_game")

    # when
    result = manager.exists("my_game")

    # then
    assert result

def test_creating_duplicates_fails(db_con):
    # given
    manager = SQLiteGameManager(db_con, num_blue=2, num_red=2, num_neutral=2)

    # when
    manager.create_random("my_game")

    # then
    with pytest.raises(GameAlreadyExistsException):
        manager.create_random("my_game")

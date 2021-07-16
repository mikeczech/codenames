import csv
import os
import sqlite3

import pytest


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

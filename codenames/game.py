from typing import Dict, Any List, Tuple, Optional
from itertools import chain
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import random

import pandas as pd
import numpy as np

from sqlite3 import Connection


class Color(Enum):
    RED = 1
    BLUE = 2


class Role(Enum):
    PLAYER = 1
    SPYMASTER = 2


@dataclass
class Word:
    id: str
    name: str
    color: str
    selected_at: Optional[datetime]

    def is_active(self):
        return bool(self.selected_at)


@dataclass
class Hint:
    word: str
    num: int


class GameState:
    @property
    def game_id(self) -> int:
        return -1

    def load(self) -> List[Word]:
        return []

    def load_hints(self) -> List[Hint]:
        return []

    def guess(self, word_id: int) -> None:
        pass

    def add_hint(self, hint: Hint) -> None:
        pass


class UnexpectedStateException(Exception):
    pass


class Game:
    def __init__(self, state: GameState):
        self._state = state

    @property
    def id(self):
        return self._state.game_id

    def get_state(self) -> Dict[str, Any]:
        return self._state.load()

    def end_turn(self) -> None:
        pass

    def add_hint(self, hint: Hint) -> None:
        self._state.add_hint(hint)

    def guess(self, word_id: int) -> None:
        self._state.guess(word_id)


class GameAlreadyExistsException(Exception):
    pass


class SQLiteGameState(GameState):
    def __init__(self, game_id: int, con: Connection):
        self._con = con
        self._game_id = game_id

    @property
    def game_id(self) -> int:
        return self._game_id

    def load(self) -> Dict[str, Any]:
        active_words = self._con.execute(
            """
            SELECT word_id, word, color, selected_at
            FROM active_words a
            LEFT JOIN words w
            ON w.id = a.word_id
            LEFT JOIN game_moves c
            ON c.game_id = a.game_id AND c.word_id  = a.word_id
            WHERE game_id = ?
            """,
            (self._game_id,),
        ).fetchall()

        active_player = self._con.execute(
            """
            SELECT color, role
            FROM turns
            WHERE game_id = ?
            ORDER BY timestamp DESC
            LIMIT 1
            """,
            (self._game_id,),
        ).fetchone()

        return {
            "words": [
                Word(w["word_id"], w["name"], w["color"], w["selected_at"])
                for w in active_words
            ],
            "active_player": {
                "color": active_player["color"],
                "role": active_player["role"],
            },
        }

        return

    def guess(self, word_id: int) -> None:
        self._con.execute(
            """
            INSERT INTO
                moves (game_id, word_id, selected_at)
            VALUES (?, ?, strftime('%s','now'))
        """,
            (self._game_id, word_id),
        )
        self._con.commit()

    def add_hint(self, hint: Hint) -> None:
        self._con.execute(
            """
            INSERT INTO
                hints (game_id, hint, num, created_at)
            VALUES (?, ?, ?, strftime('%s','now'))
        """,
            (self._game_id, hint.word, hint.num),
        )
        self._con.commit()


class SQLiteGameManager:
    def __init__(
        self,
        con: Connection,
        num_blue: int = 9,
        num_red: int = 9,
        num_neutral: int = 9,
        num_assassin: int = 1,
    ):
        self._con = con
        self._word_color_counts = {
            "blue": num_blue,
            "red": num_red,
            "neutral": num_neutral,
            "assassin": num_assassin,
        }

    def exists(self, name: str) -> bool:
        res = self._con.execute(
            "SELECT name from games WHERE name = ?", (name,)
        ).fetchone()

        if res:
            return True
        return False

    def create_random(self, name: str) -> Game:
        game = self._create_game(name)
        random_words = self._get_random_words()

        active_words = [(game.id, w.id, w.color) for w in random_words]
        self._con.executemany(
            "INSERT INTO active_words (game_id, word_id, color) VALUES (?, ?, ?);",
            active_words,
        )
        self._con.execute(
            """
            INSERT INTO
                turns (game_id, color, role, timestamp)
            VALUES (?, ?, ?, strftime('%s','now'))
                """,
            (game.id, Color.BLUE.value, Role.SPYMASTER.value),
        )

        self._con.commit()
        return game

    def get(self, name: str) -> Optional[Game]:
        return None

    def _create_game(self, name: str) -> Game:
        if self.exists(name):
            raise GameAlreadyExistsException()

        self._con.execute("INSERT INTO games (name) VALUES (?)", (name,))
        game = self._con.execute(
            "SELECT id from games WHERE name = ?", (name,)
        ).fetchone()
        return Game(SQLiteGameState(game["id"], self._con))

    def _get_random_words(self) -> List[Word]:
        words = self._con.execute(
            "SELECT id, word from words ORDER BY RANDOM() LIMIT ?",
            (sum(self._word_color_counts.values()),),
        ).fetchall()
        random_colors = self._get_random_colors()
        return [Word(w["id"], w["word"], c, None) for w, c in zip(words, random_colors)]

    def _get_random_colors(self) -> List[str]:
        ret = list(
            chain(
                *[[color] * count for color, count in self._word_color_counts.items()]
            )
        )
        random.shuffle(ret)
        return ret

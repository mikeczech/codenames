from typing import Dict, Union, Any, List, Tuple, Optional
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
    NEUTRAL = 3
    ASSASSIN = 4

    def toggle(self):
        return Color.BLUE if self == Color.RED else Color.RED


class Role(Enum):
    PLAYER = 1
    SPYMASTER = 2

    def toggle(self):
        return Role.PLAYER if self == Role.SPYMASTER else Role.PLAYER


class Condition(Enum):
    NOT_STARTED = 1
    RED_SPY = 2
    RED_PLAYER = 3
    BLUE_SPY = 4
    BLUE_PLAYER = 5
    FINISHED = 6


NUM_PLAYERS = 4


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

    def start_game(self) -> None:
        pass

    def add_player(
        self, session_id: str, is_admin: bool, color: Color, role: Role
    ) -> None:
        pass

    def remove_player(self, session_id: str) -> None:
        pass

    def load(self) -> Dict[str, Any]:
        return {}

    def guess(self, word_id: int) -> None:
        pass

    def add_hint(self, word: str, num: int) -> None:
        pass

    def commit(self) -> None:
        pass


class StateException(Exception):
    def __init__(self, message: str):
        super().__init__(message)


def load_state(func):
    def wrapper(*args):
        state = args[0]._state.load()
        func(*(args + (state,)))
    return wrapper

class Game:
    def __init__(self, state: GameState):
        self._state = state
        self._session_id = None
        self._is_admin = None
        self._color = None
        self._role = None

    @property
    def id(self):
        return self._state.game_id

    @property
    def color(self):
        return self._color

    @property
    def role(self):
        return self._role

    def get_state(self) -> Dict[str, Any]:
        return self._state.load()

    def start(self) -> None:
        if not self._is_admin:
            raise StateException("Only an admin can start a game")
        self._state.start_game()

    def join(self, session_id: str, is_admin: bool, color: Color, role: Role) -> None:
        self._state.add_player(session_id, is_admin, color, role)
        self._session_id = session_id
        self._is_admin = is_admin
        self._color = color
        self._role = role

    def leave(self) -> None:
        if not self._session_id:
            raise StateException("You have not joined a game")
        self._state.remove_player(self._session_id)
        self._session_id = None
        self._is_admin = None
        self._color = None
        self._role = None

    def end_turn(self) -> None:
        pass

    def add_hint(self, word: str, num: int) -> None:
        pass

    @load_state
    def guess(self, word_id: int, state: Dict[str, Any]) -> None:
        current_hint = state["hints"][-1]
        if current_hint["color"] != self._color:
            raise StateException("It's not your turn")

        # turns made on the current hint
        turns = [t for t in state["turns"] if t["hint_id"] == current_hint["id"]]
        if len(turns) >= current_hint["num"] + 1:
            self.end_turn()
            return

        self._state.guess(word_id)


class GameAlreadyExistsException(Exception):
    pass


class SQLiteGameState(GameState):
    def __init__(self, game_id: int, con: Connection):
        self._game_id = game_id
        self._con = con

    @property
    def game_id(self) -> int:
        return self._game_id

    def load(self) -> Dict[str, Any]:
        active_words = self._con.execute(
            """
            SELECT a.word_id, value, color, selected_at
            FROM active_words a
            LEFT JOIN words w
            ON w.id = a.word_id
            LEFT JOIN moves c
            ON c.game_id = a.game_id AND c.word_id  = a.word_id
            WHERE a.game_id = ?
            """,
            (self._game_id,),
        ).fetchall()

        hints = self._con.execute(
            """
            SELECT hint, num, color, created_at
            FROM hints
            WHERE game_id = ?
            ORDER BY id ASC
            """,
            (self._game_id,),
        ).fetchall()

        players = self._con.execute(
            """
            SELECT session_id, color, role, is_admin
            FROM players
            WHERE game_id = ?
            """,
            (self._game_id,),
        ).fetchall()

        latest_turn = self._con.execute(
            """
            SELECT condition
            FROM turns
            WHERE game_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (self._game_id,),
        ).fetchone()

        return {
            "words": [
                {
                    "id": w[0],
                    "value": w[1],
                    "color": Color(w[2]),
                    "selected_at": w[3],
                }
                for w in active_words
            ],
            "hints": [
                {
                    "word": h[0],
                    "num": h[1],
                    "color": Color(h[2]),
                    "created_at": h[3],
                }
                for h in hints
            ],
            "players": [
                {
                    "session_id": p[0],
                    "color": Color(p[1]),
                    "role": Role(p[2]),
                    "is_admin": bool(p[3]),
                }
                for p in players
            ],
            "metadata": {"condition": Condition(latest_turn[0])},
        }

    def guess(self, word_id: int) -> None:
        self._con.execute(
            """
            INSERT INTO
                moves (game_id, word_id, selected_at)
            VALUES (?, ?, strftime('%s','now'))
        """,
            (self._game_id, word_id),
        )

    def add_hint(self, word: str, num: int, color: Color) -> None:
        self._con.execute(
            """
            INSERT INTO
                hints (game_id, hint, num, color, created_at)
            VALUES (?, ?, ?, ?, strftime('%s','now'))
        """,
            (self._game_id, word, num, color.value),
        )

    def _has_started(self) -> bool:
        current_turn = self._con.execute(
            """
            SELECT condition
            FROM turns
            WHERE game_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (self._game_id,),
        ).fetchone()
        return current_turn[0] != Condition.NOT_STARTED.value

    def _is_ready(self) -> bool:
        players = self._con.execute(
            """
            SELECT COUNT(*) AS count
            FROM players
            WHERE game_id = ?
            LIMIT 1
            """,
            (self._game_id,),
        ).fetchone()
        return players[0] == NUM_PLAYERS

    def start_game(self) -> None:
        if self._has_started():
            raise StateException(f"Game {self._game_id} has already started.")

        if not self._is_ready():
            raise StateException(f"Game {self._game_id} is not ready.")

        self._con.execute(
            """
            INSERT INTO
                turns (game_id, condition, created_at)
            VALUES (?, ?, strftime('%s','now'))
        """,
            (self._game_id, Condition.BLUE_SPY.value),
        )

    def _color_role_is_occupied(self, color: Color, role: Role) -> bool:
        players = self._con.execute(
            """
            SELECT session_id
            FROM players
            WHERE game_id = ? AND color = ? AND role = ?
            """,
            (self._game_id, color.value, role.value),
        ).fetchone()
        return bool(players)

    def add_player(
        self, session_id: str, is_admin: bool, color: Color, role: Role
    ) -> None:
        if self._color_role_is_occupied(color, role):
            raise StateException(
                f"A player with color {color} and role {Role} already exists."
            )

        self._con.execute(
            """
            INSERT INTO
                players (game_id, session_id, color, role, is_admin)
            VALUES (?, ?, ?, ?, ?)
        """,
            (self._game_id, session_id, color.value, role.value, is_admin),
        )

    def _player_exists(self, session_id: str) -> bool:
        players = self._con.execute(
            """
            SELECT 1
            FROM players
            WHERE game_id = ? AND session_id = ?
            """,
            (self._game_id, session_id),
        ).fetchone()
        return bool(players)

    def remove_player(self, session_id: str) -> None:
        if not self._player_exists(session_id):
            raise StateException(f"Player with session id {session_id} does not exist.")
        self._con.execute(
            """
            DELETE FROM players
            WHERE game_id = ? AND session_id = ?
        """,
            (self._game_id, session_id),
        )

    def commit(self) -> None:
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
            Color.BLUE.value: num_blue,
            Color.RED.value: num_red,
            Color.NEUTRAL.value: num_neutral,
            Color.ASSASSIN.value: num_assassin,
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
                turns (game_id, condition, created_at)
            VALUES (?, ?, strftime('%s','now'))
                """,
            (game.id, Condition.NOT_STARTED.value),
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
        return Game(SQLiteGameState(game[0], self._con))

    def _get_random_words(self) -> List[Word]:
        words = self._con.execute(
            "SELECT id, value from words ORDER BY RANDOM() LIMIT ?",
            (sum(self._word_color_counts.values()),),
        ).fetchall()
        random_colors = self._get_random_colors()
        return [Word(w[0], w[1], c, None) for w, c in zip(words, random_colors)]

    def _get_random_colors(self) -> List[str]:
        ret = list(
            chain(
                *[[color] * count for color, count in self._word_color_counts.items()]
            )
        )
        random.shuffle(ret)
        return ret

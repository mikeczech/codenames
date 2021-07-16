from typing import Dict, Union, Any, List, Tuple, Optional
from itertools import chain
from datetime import datetime
import logging
from dataclasses import dataclass
from enum import Enum
import random
from abc import ABC

import pandas as pd
import numpy as np

from sqlite3 import Connection

LOGGER = logging.getLogger("game")


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
    value: str
    color: Color
    selected_at: Optional[datetime]

    def is_active(self):
        return bool(self.selected_at)


class GamePersister(ABC):
    @property
    def game_id(self) -> int:
        raise NotImplementedError()

    def start_game(self) -> None:
        raise NotImplementedError()

    def add_player(
        self, session_id: str, is_admin: bool, color: Color, role: Role
    ) -> None:
        raise NotImplementedError()

    def remove_player(self, session_id: str) -> None:
        raise NotImplementedError()

    def load(self) -> Dict[str, Any]:
        raise NotImplementedError()

    def add_guess(self, word_id: int) -> None:
        raise NotImplementedError()

    def add_hint(self, word: str, num: int) -> None:
        raise NotImplementedError()

    def is_occupied(self, color: Color, role: Role) -> bool:
        raise NotImplementedError()

    def has_joined(self, session_id: str) -> bool:
        raise NotImplementedError()

    def commit(self) -> None:
        raise NotImplementedError()


class StateException(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self._message = message

    @property
    def message(self):
        return self._message


class GuessesExceededException(Exception):
    def __init__(self):
        super().__init__()


class GameState(ABC):
    def __init__(self, session_id: str, is_admin: bool, persister: GamePersister):
        self._persister = persister
        self._session_id = session_id
        self._is_admin = is_admin

    @property
    def persister(self) -> GamePersister:
        return self._persister

    @property
    def session_id(self) -> str:
        return self._session_id

    @property
    def is_admin(self) -> bool:
        return self._is_admin

    def get_info(self) -> Dict[str, Any]:
        return self._persister.load()

    def start_game(self) -> None:
        raise NotImplementedError()

    def join(self, color: Color, role: Role) -> None:
        raise NotImplementedError()

    def guess(self, word_id: int) -> None:
        raise NotImplementedError()

    def give_hint(self, word: str, num: int) -> None:
        raise NotImplementedError()

    def end_turn(self) -> None:
        raise NotImplementedError()


class NotStartedGameState(GameState):
    def __init__(self, session_id: str, is_admin: bool, persister: GamePersister):
        super().__init__(session_id, is_admin, persister)

    def start_game(self) -> None:
        conditions = [
            self._persister.is_occupied(Color.RED, Role.PLAYER),
            self._persister.is_occupied(Color.BLUE, Role.PLAYER),
            self._persister.is_occupied(Color.RED, Role.SPYMASTER),
            self._persister.is_occupied(Color.BLUE, Role.SPYMASTER),
        ]
        if not all(conditions):
            raise StateException("The game is not ready.")
        self._persister.start_game()

    def join(self, color: Color, role: Role) -> None:
        if self._persister.has_joined(self._session_id):
            raise StateException(
                f"Session ID {self._session_id} has already joined the game."
            )
        if self._persister.is_occupied(color, role):
            raise StateException(
                f"Color {color} and role {role} is not available anymore."
            )
        self._persister.add_player(self._session_id, self._is_admin, color, role)

    def guess(self, word_id: int) -> None:
        raise StateException("The game has not started yet.")

    def give_hint(self, word: str, num: int) -> None:
        raise StateException("The game has not started yet.")

    def end_turn(self) -> None:
        raise StateException("The game has not started yet.")


class SpyTurnGameState(GameState):
    def __init__(
        self, session_id: str, is_admin: bool, persister: GamePersister, color: Color
    ):
        super().__init__(session_id, is_admin, persister)
        self._color = color

    def start_game(self) -> None:
        raise StateException("The game has already started")

    def join(self, color: Color, role: Role) -> None:
        raise StateException("The game has already started")

    def guess(self, word_id: int) -> None:
        raise StateException("A spy can give hints only")

    def end_turn(self) -> None:
        raise StateException("A spy must provide a hint")

    def give_hint(self, word: str, num: int) -> None:
        pass


class PlayerTurnGameState(GameState):
    def __init__(
        self, session_id: str, is_admin: bool, persister: GamePersister, color: Color
    ):
        super().__init__(session_id, is_admin, persister)
        self._color = color

    def _count_remaining_guesses(self) -> int:
        game_info = self.persister.load()
        latest_hint = game_info["hints"][-1]
        round_turns = []
        for t in game_info["turns"]:
            if t["hint_id"] == latest_hint["id"]:
                t.append(round_turns)
        return (latest_hint["num"] + 1) - len(round_turns)

    def start_game(self) -> None:
        raise StateException("The game has already started")

    def join(self, color: Color, role: Role) -> None:
        raise StateException("The game has already started")

    def give_hint(self, word: str, num: int) -> None:
        raise StateException("A player cannot give hints")

    def guess(self, word_id: int) -> None:
        # TODO verify word id
        self._persister.add_guess(word_id)
        if self._count_remaining_guesses() == 0:
            self.end_turn()

        if self._color == Color.BLUE:
            return PlayerTurnGameState(
                self.session_id, self.is_admin, self.persister, Color.BLUE
            )
        return PlayerTurnGameState(
            self.session_id, self.is_admin, self.persister, Color.RED
        )

    def end_turn(self) -> None:
        if self._color == Color.BLUE:
            return SpyTurnGameState(
                self.session_id, self.is_admin, self.persister, Color.RED
            )
        return SpyTurnGameState(
            self.session_id, self.is_admin, self.persister, Color.BLUE
        )


class FinishedGameState(GameState):
    def __init__(self, session_id: str, is_admin: bool, persister: GamePersister):
        super().__init__(session_id, is_admin, persister)


class Game:
    def __init__(self, session_id: str, is_admin: bool, persister: GamePersister):
        self._session_id = session_id
        self._is_admin = is_admin
        self._persister = persister

    @property
    def id(self):
        return self._persister.game_id

    def load_state(self) -> GameState:
        game_info = self._persister.load()
        condition = game_info["metadata"]["condition"]
        if condition == Condition.NOT_STARTED:
            return NotStartedGameState(
                self._session_id, self._is_admin, self._persister
            )
        elif condition == Condition.RED_SPY:
            return SpyTurnGameState(
                self._session_id, self._is_admin, self._persister, Color.RED
            )
        elif condition == Condition.BLUE_SPY:
            return SpyTurnGameState(
                self._session_id, self._is_admin, self._persister, Color.BLUE
            )
        elif condition == Condition.RED_PLAYER:
            return PlayerTurnGameState(
                self._session_id, self._is_admin, self._persister, Color.RED
            )
        elif condition == Condition.BLUE_PLAYER:
            return PlayerTurnGameState(
                self._session_id, self._is_admin, self._persister, Color.BLUE
            )
        else:
            raise Exception()


class GameAlreadyExistsException(Exception):
    pass


class SQLiteGamePersister(GamePersister):
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
                Word(id=w[0], value=w[1], color=Color(w[2]), selected_at=w[3])
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

    def add_guess(self, word_id: int) -> None:
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

    def has_joined(self, session_id: str) -> bool:
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
        if not self.has_joined(session_id):
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

    def create_random(self, name: str, session_id: str) -> Game:
        game = self._create_game(name, session_id)
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

    def _create_game(self, name: str, session_id: str) -> Game:
        if self.exists(name):
            raise GameAlreadyExistsException()

        self._con.execute("INSERT INTO games (name) VALUES (?)", (name,))
        game = self._con.execute(
            "SELECT id from games WHERE name = ?", (name,)
        ).fetchone()
        return Game(session_id, True, SQLiteGamePersister(game[0], self._con))

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

from typing import Dict, Union, Any, List, Tuple, Optional
from itertools import chain
import random

from codenames.game import (
    GameBackend,
    Game,
    Color,
    Role,
    Condition,
    GameAlreadyExistsException,
    Word,
)
from sqlite3 import Connection


class SQLiteGameBackend(GameBackend):
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
            SELECT id, hint, num, color, created_at
            FROM hints
            WHERE game_id = ?
            ORDER BY id ASC
            """,
            (self._game_id,),
        ).fetchall()

        players = self._con.execute(
            """
            SELECT session_id, color, role
            FROM players
            WHERE game_id = ?
            """,
            (self._game_id,),
        ).fetchall()

        conditions = self._con.execute(
            """
            SELECT hint_id, condition
            FROM conditions
            WHERE game_id = ?
            ORDER BY id ASC
            """,
            (self._game_id,),
        ).fetchall()

        return {
            "words": {
                w[0]: Word(id=w[0], value=w[1], color=Color(w[2]), selected_at=w[3])
                for w in active_words
            },
            "hints": [
                {
                    "id": h[0],
                    "word": h[1],
                    "num": h[2],
                    "color": Color(h[3]) if h[3] else None,
                }
                for h in hints
            ],
            "conditions": [
                {"hint_id": t[0], "value": Condition(t[1])} for t in conditions
            ],
            "players": [
                {"session_id": p[0], "color": Color(p[1]), "role": Role(p[2])}
                for p in players
            ],
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

    def add_condition(self, condition: Condition) -> None:
        self._con.execute(
            """
            INSERT INTO
                conditions (game_id, hint_id, condition, created_at)
            SELECT
                game_id,
                id AS hint_id,
                ? AS condition,
                strftime('%s','now') AS created_at
            FROM hints
            WHERE game_id = ?
            ORDER BY id DESC
            LIMIT 1
        """,
            (condition.value, self._game_id),
        )

    def is_occupied(self, color: Color, role: Role) -> bool:
        players = self._con.execute(
            """
            SELECT session_id
            FROM players
            WHERE game_id = ? AND color = ? AND role = ?
            """,
            (self._game_id, color.value, role.value),
        ).fetchone()
        return bool(players)

    def add_player(self, session_id: str, color: Color, role: Role) -> None:
        self._con.execute(
            """
            INSERT INTO
                players (game_id, session_id, color, role)
            VALUES (?, ?, ?, ?)
        """,
            (self._game_id, session_id, color.value, role.value),
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
        self._con.execute(
            """
            DELETE FROM players
            WHERE game_id = ? AND session_id = ?
        """,
            (self._game_id, session_id),
        )

    def get_active_session_id(self) -> str:
        game_condition = Condition(
            self._con.execute(
                """
                SELECT condition
                FROM conditions
                WHERE game_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (self._game_id,),
            ).fetchone()[0]
        )

        active_session_id = self._con.execute(
            """
            SELECT session_id
            FROM players
            WHERE game_id = ? AND color = ? AND role = ?
            LIMIT 1
            """,
            (self._game_id, game_condition.color.value, game_condition.role.value),
        ).fetchone()

        if not active_session_id:
            raise Exception("Could not determine active player (maybe there is none?)")

        return active_session_id[0]

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
                conditions (hint_id, game_id, condition, created_at)
            VALUES (?, ?, ?, strftime('%s','now'))
                """,
            (None, game.id, Condition.NOT_STARTED.value),
        )
        # add dummy hint for code simplification
        self._con.execute(
            """
            INSERT INTO
                hints (game_id, hint, num, color, created_at)
            VALUES (?, ?, ?, ?, strftime('%s', 'now'))
            """,
            (game.id, None, None, None),
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
        return Game(session_id, SQLiteGameBackend(game[0], self._con))

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

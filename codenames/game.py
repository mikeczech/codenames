from typing import List, Optional
from itertools import chain
from dataclasses import dataclass
import random
import hashlib

import pandas as pd
import numpy as np

from sqlite3 import Connection


def read_wordlist_csv(path: str) -> List[str]:
    return (
        pd.read_csv(path, header=None)
        .unstack()
        .reset_index(drop=True)
        .dropna()
        .str.lower()
        .values.tolist()
    )


# class Game:
#     """ Codenames game """
#
#     def __init__(self, red_words, blue_words, neutral_words, assassin_word):
#         self.__red_words = red_words
#         self.__blue_words = blue_words
#         self.__neutral_words = neutral_words
#         self.__assassin_words = assassin_word
#
#     @staticmethod
#     def create_from(wordlist: List[str]):
#         choice = np.random.choice(wordlist, size=28, replace=False)
#         red_words = choice[:9]
#         blue_words = choice[9:18]
#         neutral_words = choice[18:27]
#         assassin_word = choice[27]
#         return Game(red_words, blue_words, neutral_words, assassin_word)


@dataclass
class Word:
    id: str
    name: str


class GameState:
    def load(self, game_id: int) -> List[Word]:
        return []


class Game:
    def __init__(self, id: int, state: GameState):
        self._id = id
        self._state = state

    @property
    def id(self):
        return self._id


class GameAlreadyExistsException(Exception):
    pass


class SQLiteGameState(GameState):
    def __init__(self, con: Connection):
        self._con = con

    def load(self, game_id: int) -> List[Word]:
        return []


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
        random_colors = self._get_random_colors()
        random_words = self._get_random_words()

        active_words = [(game.id, w.id, c) for w, c in zip(random_words, random_colors)]
        self._con.executemany(
            "INSERT INTO active_words (game_id, word_id, color) VALUES (?, ?, ?);",
            active_words,
        )

        self._con.commit()
        return game

    def get(self, name: str) -> Optional[Game]:
        return None

    def _get_random_colors(self) -> List[str]:
        ret = list(
            chain(
                *[[color] * count for color, count in self._word_color_counts.items()]
            )
        )
        random.shuffle(ret)
        return ret

    def _create_game(self, name: str) -> Game:
        if self.exists(name):
            raise GameAlreadyExistsException()

        self._con.execute("INSERT INTO games (name) VALUES (?)", (name,))
        game = self._con.execute(
            "SELECT id from games WHERE name = ?", (name,)
        ).fetchone()
        return Game(game["id"], SQLiteGameState(self._con))

    def _get_random_words(self) -> List[Word]:
        words = self._con.execute(
            "SELECT id, word from words ORDER BY RANDOM() LIMIT ?",
            (sum(self._word_color_counts.values()),),
        ).fetchall()
        return [Word(w["id"], w["word"]) for w in words]

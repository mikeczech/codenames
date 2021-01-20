from typing import List

import pandas as pd
import numpy as np


def read_wordlist_csv(path: str) -> List[str]:
    return (
        pd.read_csv(path, header=None)
        .unstack()
        .reset_index(drop=True)
        .dropna()
        .values.tolist()
    )


class Game:
    """ Codenames game """

    def __init__(self, red_words, blue_words, neutral_words, assassin_word):
        self.__red_words = red_words
        self.__blue_words = blue_words
        self.__neutral_words = neutral_words
        self.__assassin_words = assassin_word

    @staticmethod
    def create_from(wordlist: List[str]):
        choice = np.random.choice(wordlist, size=28, replace=False)
        red_words = choice[:9]
        blue_words = choice[9:18]
        neutral_words = choice[18:27]
        assassin_word = choice[27]
        return Game(red_words, blue_words, neutral_words, assassin_word)

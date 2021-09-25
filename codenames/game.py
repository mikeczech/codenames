from typing import Dict, Union, Any, List, Tuple, Optional
from datetime import datetime
import logging
from dataclasses import dataclass
from enum import Enum
import random
from abc import ABC


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
    RED_WINS = 6
    BLUE_WINS = 7

    @property
    def color(self) -> Color:
        if self == self.BLUE_PLAYER or self == self.BLUE_SPY or self == self.BLUE_WINS:
            return Color.BLUE
        if self == self.RED_PLAYER or self == self.RED_SPY or self == self.RED_WINS:
            return Color.RED
        raise Exception("Cannot determine color.")

    @property
    def role(self) -> Role:
        if self == self.BLUE_PLAYER or self == self.RED_PLAYER:
            return Role.PLAYER
        if self == self.BLUE_SPY or self == self.RED_SPY:
            return Role.SPYMASTER
        raise Exception("Cannot determine role.")


NUM_PLAYERS = 4


@dataclass
class Word:
    id: str
    value: str
    color: Color
    selected_at: Optional[datetime]

    @property
    def is_active(self):
        return not bool(self.selected_at)


class GameBackend(ABC):
    @property
    def game_id(self) -> int:
        raise NotImplementedError()

    def add_condition(self, condition: Condition) -> None:
        raise NotImplementedError()

    def add_player(self, session_id: str, color: Color, role: Role) -> None:
        raise NotImplementedError()

    def remove_player(self, session_id: str) -> None:
        raise NotImplementedError()

    def load(self) -> Dict[str, Any]:
        raise NotImplementedError()

    def add_guess(self, word_id: int) -> None:
        raise NotImplementedError()

    def add_hint(self, word: str, num: int, color: Color) -> None:
        raise NotImplementedError()

    def is_occupied(self, color: Color, role: Role) -> bool:
        raise NotImplementedError()

    def get_active_session_id(self) -> str:
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


class AlreadyJoinedException(Exception):
    def __init__(self):
        super().__init__()


class RoleOccupiedException(Exception):
    def __init__(self):
        super().__init__()


class GameAlreadyExistsException(Exception):
    pass


def check_authorization(f):
    def wrapper(*args, **kwargs):
        active_session_id = args[0].backend.get_active_session_id()
        if active_session_id != args[0].session_id:
            raise Exception("It's not your turn!")
        return f(*args, **kwargs)

    return wrapper


class GameState(ABC):
    def __init__(self, session_id: str, backend: GameBackend):
        self._backend = backend
        self._session_id = session_id

    @property
    def backend(self) -> GameBackend:
        return self._backend

    @property
    def session_id(self) -> str:
        return self._session_id

    def get_info(self) -> Dict[str, Any]:
        return self._backend.load()

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
    def __init__(self, session_id: str, backend: GameBackend):
        super().__init__(session_id, backend)

    def start_game(self) -> None:
        if self.get_info()["conditions"][-1]["value"] != Condition.NOT_STARTED:
            raise StateException("Game has already been started.")

        conditions = [
            self._backend.is_occupied(Color.RED, Role.PLAYER),
            self._backend.is_occupied(Color.BLUE, Role.PLAYER),
            self._backend.is_occupied(Color.RED, Role.SPYMASTER),
            self._backend.is_occupied(Color.BLUE, Role.SPYMASTER),
        ]
        if not all(conditions):
            raise StateException("The game is not ready.")
        self.backend.add_condition(Condition.BLUE_SPY)
        self.backend.commit()

    def join(self, color: Color, role: Role) -> None:
        if self.backend.is_occupied(color, role):
            raise RoleOccupiedException()
        if self.backend.has_joined(self._session_id):
            raise AlreadyJoinedException()
        self.backend.add_player(self._session_id, color, role)
        self.backend.commit()

    def guess(self, word_id: int) -> None:
        raise StateException("The game has not started yet.")

    def give_hint(self, word: str, num: int) -> None:
        raise StateException("The game has not started yet.")

    def end_turn(self) -> None:
        raise StateException("The game has not started yet.")


class SpyTurnGameState(GameState):
    def __init__(self, session_id: str, backend: GameBackend, color: Color):
        super().__init__(session_id, backend)
        self._color = color

    def start_game(self) -> None:
        raise StateException("The game has already started")

    def join(self, color: Color, role: Role) -> None:
        raise StateException("The game has already started")

    @check_authorization
    def guess(self, word_id: int) -> None:
        raise StateException("A spy can give hints only")

    @check_authorization
    def end_turn(self) -> None:
        raise StateException("A spy must provide a hint")

    @check_authorization
    def give_hint(self, word: str, num: int) -> None:
        hint_id = self.backend.add_hint(word, num, self._color)
        if self._color == Color.BLUE:
            self.backend.add_condition(Condition.BLUE_PLAYER, hint_id)
        elif self._color == Color.RED:
            self.backend.add_condition(Condition.RED_PLAYER, hint_id)
        else:
            raise StateException("Cannot handle color '{self._color}'")
        self.backend.commit()


class PlayerTurnGameState(GameState):
    def __init__(self, session_id: str, backend: GameBackend, color: Color):
        super().__init__(session_id, backend)
        self._color = color

    def _count_remaining_guesses(self, game_info) -> int:
        latest_hint = game_info["hints"][-1]
        round_conditions = []
        for t in game_info["conditions"]:
            if t["hint_id"] == latest_hint["id"]:
                round_conditions.append(t)
        return (latest_hint["num"] + 1) - len(round_conditions)

    def _count_num_words_left(self, game_info) -> Tuple[int, int]:
        num_blue_words_left = 0
        num_red_words_left = 0
        for w in game_info["words"].values():
            if w.is_active:
                if w.color == Color.RED:
                    num_red_words_left += 1
                elif w.color == Color.BLUE:
                    num_blue_words_left += 1
        return num_blue_words_left, num_red_words_left

    def start_game(self) -> None:
        raise StateException("The game has already started")

    def join(self, color: Color, role: Role) -> None:
        raise StateException("The game has already started")

    @check_authorization
    def give_hint(self, word: str, num: int) -> None:
        raise StateException("A player cannot give hints")

    @check_authorization
    def guess(self, word_id: int) -> None:
        game_info = self.get_info()

        if (
            word_id not in game_info["words"]
            or not game_info["words"][word_id].is_active
        ):
            raise StateException(
                f"Word with id {word_id} is either not active or does not exist."
            )

        num_blue_words_left, num_red_words_left = self._count_num_words_left(game_info)
        guessed_color = game_info["words"][word_id].color

        num_remaining_guesses = self._count_remaining_guesses(game_info)
        if num_remaining_guesses == 0:
            self.end_turn()
        else:
            self.backend.add_guess(word_id)

            # determine next game condition
            if guessed_color == Color.NEUTRAL:
                self.end_turn(do_commit=False)
            elif self._color == Color.BLUE and guessed_color == Color.RED:
                if num_red_words_left == 1:
                    self.backend.add_condition(Condition.RED_WINS)
                else:
                    self.end_turn(do_commit=False)
            elif self._color == Color.RED and guessed_color == Color.BLUE:
                if num_blue_words_left == 1:
                    self.backend.add_condition(Condition.BLUE_WINS)
                else:
                    self.end_turn(do_commit=False)
            elif self._color == Color.BLUE and guessed_color == Color.BLUE:
                if num_blue_words_left == 1:
                    self.backend.add_condition(Condition.BLUE_WINS)
                else:
                    self.backend.add_condition(Condition.BLUE_PLAYER)
            elif self._color == Color.RED and guessed_color == Color.RED:
                if num_red_words_left == 1:
                    self.backend.add_condition(Condition.RED_WINS)
                else:
                    self.backend.add_condition(Condition.RED_PLAYER)
            elif self._color == Color.BLUE and guessed_color == Color.ASSASSIN:
                self.backend.add_condition(Condition.RED_WINS)
            elif self._color == Color.RED and guessed_color == Color.ASSASSIN:
                self.backend.add_condition(Condition.BLUE_WINS)
            else:
                raise StateException(f"Cannot handle guess of word id {word_id}.")

            self.backend.commit()

    @check_authorization
    def end_turn(self, do_commit: bool = True) -> None:
        if self._color == Color.BLUE:
            self.backend.add_condition(Condition.RED_SPY)
        elif self._color == Color.RED:
            self.backend.add_condition(Condition.BLUE_SPY)
        else:
            raise StateException(f"Cannot handle color {self._color}.")

        if do_commit:
            self.backend.commit()


class FinishedGameState(GameState):
    def __init__(self, session_id: str, backend: GameBackend):
        super().__init__(session_id, backend)


class Game:
    def __init__(self, session_id: str, backend: GameBackend):
        self._session_id = session_id
        self._backend = backend

    @property
    def id(self):
        return self._backend.game_id

    def load_state(self) -> GameState:
        game_info = self._backend.load()
        condition = game_info["conditions"][-1]["value"]
        if condition == Condition.NOT_STARTED:
            return NotStartedGameState(self._session_id, self._backend)
        elif condition == Condition.RED_SPY:
            return SpyTurnGameState(self._session_id, self._backend, Color.RED)
        elif condition == Condition.BLUE_SPY:
            return SpyTurnGameState(self._session_id, self._backend, Color.BLUE)
        elif condition == Condition.RED_PLAYER:
            return PlayerTurnGameState(self._session_id, self._backend, Color.RED)
        elif condition == Condition.BLUE_PLAYER:
            return PlayerTurnGameState(self._session_id, self._backend, Color.BLUE)
        else:
            raise Exception()

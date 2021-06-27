from unittest.mock import MagicMock
import pytest

from codenames.game import (
    Condition,
    Game,
    Color,
    GuessesExceededException,
    Role,
    StateException,
)

from utils import create_default_game, add_players


class TestGame:
    def test_join(self):
        # given
        state = MagicMock()
        game = Game(state)

        # when
        game.join("A100", False, Color.RED, Role.PLAYER)

        # then
        state.add_player.assert_called_with("A100", False, Color.RED, Role.PLAYER)
        assert game.color == Color.RED
        assert game.role == Role.PLAYER

    def test_guessing_requires_join(self):
        # given
        game = Game(MagicMock())

        # when / then
        with pytest.raises(StateException) as ex:
            game.guess(11)

        assert ex.value.message == "You have not joined the game yet."

    def test_guessing_requires_a_hint(self):
        # given
        game = Game(MagicMock())
        game.join("A100", False, Color.RED, Role.PLAYER)

        # when / then
        with pytest.raises(StateException) as ex:
            game.guess(11)

        assert ex.value.message == "No hint given. This should not happen."

    def test_guess(self):
        # given
        state = MagicMock()
        state.load.return_value = {
            "hints": [{"color": Color.RED, "word": "foo", "num": 2}],
            "turns": [],
            "metadata": {"condition": Condition.RED_PLAYER},
        }
        game = Game(state)
        game.join("A100", False, Color.RED, Role.PLAYER)

        # when
        game.guess(11)

        # then
        state.add_guess.assert_called_with(11)

    def test_guessing_fails_if_spy_turn(self):
        # given
        state = MagicMock()
        state.load.return_value = {
            "metadata": {"condition": Condition.RED_SPY},
        }
        game = Game(state)
        game.join("A100", False, Color.RED, Role.PLAYER)

        # when / then
        with pytest.raises(StateException) as ex:
            game.guess(11)

        assert ex.value.message == "Still waiting for a hint."

    def test_guess_fails_if_wrong_turn(self):
        # given
        state = MagicMock()
        state.load.return_value = {
            "metadata": {"condition": Condition.BLUE_PLAYER},
        }
        game = Game(state)
        game.join("A100", False, Color.RED, Role.PLAYER)

        # when / then
        with pytest.raises(StateException) as ex:
            game.guess(11)

        assert ex.value.message == "It's BLUEs turn."

    def test_num_of_guesses_is_limited(self):
        # given
        state = MagicMock()
        state.load.return_value = {
            "hints": [{"id": 23, "color": Color.RED, "word": "foo", "num": 2}],
            "turns": [
                {"hint_id": 23} for _ in range(3)
            ],  # we already have three guesses for hint 24
            "metadata": {"condition": Condition.RED_PLAYER},
        }
        game = Game(state)
        game.join("A100", False, Color.RED, Role.PLAYER)

        # when / then
        with pytest.raises(GuessesExceededException):
            game.guess(11)

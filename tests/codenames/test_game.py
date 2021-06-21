from unittest.mock import MagicMock
import pytest

from codenames.game import Game, Color, GuessesExceededException, Role, StateException


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

    def test_guess(self):
        # given
        state = MagicMock()
        state.load.return_value = {
            "hints": [{"color": Color.RED, "word": "foo", "num": 2}],
            "turns": [],
        }
        game = Game(state)
        game.join("A100", False, Color.RED, Role.PLAYER)

        # when
        game.guess(11)

        # then
        state.guess.assert_called_with(11)

    def test_num_of_guesses_is_limited(self):
        # given
        state = MagicMock()
        state.load.return_value = {
            "hints": [{"id": 23, "color": Color.RED, "word": "foo", "num": 2}],
            "turns": [
                {"hint_id": 23} for _ in range(3)
            ],  # we already have three guesses for hint 24
        }
        game = Game(state)
        game.join("A100", False, Color.RED, Role.PLAYER)

        # when / then
        with pytest.raises(GuessesExceededException):
            game.guess(11)

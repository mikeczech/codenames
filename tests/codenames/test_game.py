from unittest.mock import MagicMock
import pytest

from codenames.game import Game, Color, Role

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
            "turns": []
        }
        game = Game(state)
        game.join("A100", False, Color.RED, Role.PLAYER)


        # when
        game.guess(11)

        # then
        state.guess.assert_called_with(11)

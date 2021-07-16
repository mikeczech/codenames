from unittest.mock import MagicMock
import pytest

from codenames.game import NotStartedGameState, StateException


class TestGameState:
    def test_invalid_invocations(self):
        # given
        state = NotStartedGameState("mysessionid", False, MagicMock())

        # when / then
        with pytest.raises(StateException):
            state.guess(0)

        with pytest.raises(StateException):
            state.give_hint("myhint", 2)

        with pytest.raises(StateException):
            state.end_turn()

from unittest.mock import MagicMock
from pytest import fixture
import pytest

from codenames.game import (
    AlreadyJoinedException,
    Color,
    Condition,
    NotStartedGameState,
    Role,
    RoleOccupiedException,
    SQLiteGamePersister,
    StateException,
)
from utils import create_default_game, add_players


class TestNotStartedGameState:
    @fixture
    def persister(self, db_con):
        persister = SQLiteGamePersister(42, db_con)
        create_default_game(db_con)
        return persister

    def test_invalid_invocations(self, persister):
        # given
        state = NotStartedGameState("mysessionid", False, persister)

        # when / then
        with pytest.raises(StateException):
            state.guess(0)

        with pytest.raises(StateException):
            state.give_hint("myhint", 2)

        with pytest.raises(StateException):
            state.end_turn()

    def test_cannot_join_twice(self, persister):
        # given
        state = NotStartedGameState("mysessionid", False, persister)

        # when / then
        with pytest.raises(AlreadyJoinedException):
            state.join(Color.RED, Role.PLAYER)
            state.join(Color.BLUE, Role.PLAYER)

    def test_cannot_join_already_occupied_role(self, persister):
        # given
        state = NotStartedGameState("mysessionid", False, persister)

        # when / then
        with pytest.raises(RoleOccupiedException):
            state.join(Color.RED, Role.PLAYER)
            state.join(Color.RED, Role.PLAYER)

    def test_start_game_fails_if_any_role_is_still_open(self, persister):
        # given
        state = NotStartedGameState("mysessionid", False, persister)

        # when / then
        with pytest.raises(StateException):
            state.start_game()

    def test_start_game_foo(self, db_con, persister):
        # given
        state = NotStartedGameState("mysessionid", False, persister)
        add_players(db_con)

        # when
        pre_condition = state.get_info()["metadata"]["condition"]
        state.start_game()
        post_condition = state.get_info()["metadata"]["condition"]

        # then
        assert pre_condition == Condition.NOT_STARTED
        assert post_condition == Condition.BLUE_SPY

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
    SpyTurnGameState,
    StateException,
)
from utils import create_default_game, add_players


class TestNotStartedGameState:
    @fixture
    def persister(self, db_con):
        persister = SQLiteGamePersister(42, db_con)
        create_default_game(db_con)
        return persister

    @fixture
    def not_started_state(self, persister):
        return NotStartedGameState("mysessionid", False, persister)

    def test_invalid_invocations(self, not_started_state):
        # when / then
        with pytest.raises(StateException):
            not_started_state.guess(0)

        with pytest.raises(StateException):
            not_started_state.give_hint("myhint", 2)

        with pytest.raises(StateException):
            not_started_state.end_turn()

    def test_cannot_join_twice(self, not_started_state):
        # when / then
        with pytest.raises(AlreadyJoinedException):
            not_started_state.join(Color.RED, Role.PLAYER)
            not_started_state.join(Color.BLUE, Role.PLAYER)

    def test_cannot_join_already_occupied_role(self, not_started_state):
        # when / then
        with pytest.raises(RoleOccupiedException):
            not_started_state.join(Color.RED, Role.PLAYER)
            not_started_state.join(Color.RED, Role.PLAYER)

    def test_start_game_fails_if_any_role_is_still_open(self, not_started_state):
        # when / then
        with pytest.raises(StateException):
            not_started_state.start_game()

    def test_start_game_foo(self, db_con, not_started_state):
        # given
        add_players(db_con)

        # when
        pre_condition = not_started_state.get_info()["metadata"]["condition"]
        not_started_state.start_game()
        post_condition = not_started_state.get_info()["metadata"]["condition"]

        # then
        assert pre_condition == Condition.NOT_STARTED
        assert post_condition == Condition.BLUE_SPY

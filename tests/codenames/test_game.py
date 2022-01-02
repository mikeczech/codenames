from unittest.mock import MagicMock
from pytest import fixture
import pytest

from codenames.game import (
    AlreadyJoinedException,
    Color,
    Condition,
    NotStartedGameState,
    PlayerTurnGameState,
    Role,
    RoleOccupiedException,
    InvalidColorRoleCombination,
    SpyTurnGameState,
    StateException,
)
from codenames.sql import SQLAlchemyGameBackend
from utils import create_default_game, add_players


class TestNotStartedGameState:
    @fixture
    def backend(self, db_session):
        backend = SQLAlchemyGameBackend(42, db_session)
        create_default_game(db_session)
        return backend

    @fixture
    def not_started_state(self, backend):
        return NotStartedGameState("mysessionid", backend)

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
            not_started_state.join(Color.RED, Role.PLAYER, "ben")
            not_started_state.join(Color.BLUE, Role.PLAYER, "lisa")

    def test_cannot_join_as_neutral_color(self, not_started_state):
        # when / then
        with pytest.raises(InvalidColorRoleCombination):
            not_started_state.join(Color.NEUTRAL, Role.PLAYER, "bernd")

    def test_cannot_join_as_assassin_color(self, not_started_state):
        # when / then
        with pytest.raises(InvalidColorRoleCombination):
            not_started_state.join(Color.ASSASSIN, Role.PLAYER, "chuck")

    def test_cannot_join_already_occupied_role(self, not_started_state):
        # when / then
        with pytest.raises(RoleOccupiedException):
            not_started_state.join(Color.RED, Role.PLAYER, "mike")
            not_started_state.join(Color.RED, Role.PLAYER, "jan")

    def test_start_game_fails_if_any_role_is_still_open(self, not_started_state):
        # when / then
        with pytest.raises(StateException):
            not_started_state.start_game()

    def test_start_game_foo(self, db_session, not_started_state):
        # given
        add_players(db_session)

        # when
        pre_condition = not_started_state.get_info()["conditions"][-1]["value"]
        not_started_state.start_game()
        post_condition = not_started_state.get_info()["conditions"][-1]["value"]

        # then
        assert pre_condition == Condition.NOT_STARTED
        assert post_condition == Condition.BLUE_SPY

    def test_cannot_start_game_twice(self, db_session, not_started_state):
        # given
        add_players(db_session)

        # when / then
        with pytest.raises(StateException):
            not_started_state.start_game()
            not_started_state.start_game()


class TestSpyTurnGameState:
    @fixture
    def backend(self, db_session):
        backend = SQLAlchemyGameBackend(42, db_session)
        create_default_game(db_session)
        add_players(db_session)
        return backend

    @fixture
    def blue_spy_turn_state(self, backend):
        return SpyTurnGameState("A100", backend, Color.BLUE)

    @fixture
    def red_spy_turn_state(self, backend):
        return SpyTurnGameState("A22", backend, Color.RED)

    def test_invalid_invocations(self, blue_spy_turn_state):
        # when / then
        with pytest.raises(Exception):
            blue_spy_turn_state.guess(0)

        with pytest.raises(Exception):
            blue_spy_turn_state.start_game()

        with pytest.raises(Exception):
            blue_spy_turn_state.join(Color.RED, Role.PLAYER, "andreas")

        with pytest.raises(Exception):
            blue_spy_turn_state.end_turn()

    @pytest.mark.parametrize(
        "spy_turn_state, initial_condition, color, final_condition",
        [
            ("red_spy_turn_state", Condition.RED_SPY, Color.RED, Condition.RED_PLAYER),
            (
                "blue_spy_turn_state",
                Condition.BLUE_SPY,
                Color.BLUE,
                Condition.BLUE_PLAYER,
            ),
        ],
    )
    def test_give_hint(
        self, spy_turn_state, initial_condition, color, final_condition, request
    ):
        # given
        spy_turn_state = request.getfixturevalue(spy_turn_state)
        spy_turn_state.backend.add_condition(initial_condition)

        # when
        pre_condition = spy_turn_state.get_info()["conditions"][-1]["value"]
        spy_turn_state.give_hint("myhint", 2)

        post_game_info = spy_turn_state.get_info()
        post_condition = post_game_info["conditions"][-1]["value"]
        latest_hint = post_game_info["hints"][-1]

        # then
        assert pre_condition == initial_condition
        assert post_condition == final_condition
        assert latest_hint["word"] == "myhint"
        assert latest_hint["num"] == 2
        assert latest_hint["color"] == color


class TestPlayerTurnGameState:
    @fixture
    def backend(self, db_session):
        backend = SQLAlchemyGameBackend(42, db_session)
        create_default_game(db_session)
        add_players(db_session)
        return backend

    @fixture
    def blue_player_turn_state(self, backend):
        latest_hint_id = backend.add_hint("myhint", 1, Color.BLUE)
        backend.add_condition(Condition.BLUE_PLAYER, latest_hint_id)
        return PlayerTurnGameState("A21", backend, Color.BLUE)

    def test_invalid_invocations(self, blue_player_turn_state):
        # when / then
        with pytest.raises(Exception):
            blue_player_turn_state.give_hint("myword", 2)

        with pytest.raises(Exception):
            blue_player_turn_state.start_game()

        with pytest.raises(Exception):
            blue_player_turn_state.join(Color.RED, Role.PLAYER, "judith")

    def test_cannot_guess_already_selected_word(self, backend, blue_player_turn_state):
        # when / then
        with pytest.raises(StateException):
            blue_player_turn_state.guess(42)  # word id 42 does not exist

    def test_guess_correct_word(self, blue_player_turn_state):
        # when
        game_info = blue_player_turn_state.get_info()
        pre_condition = game_info["words"][2].is_active

        blue_player_turn_state.guess(2)  # guessed word is blue

        game_info = blue_player_turn_state.get_info()
        post_condition = game_info["words"][2].is_active

        # then
        assert pre_condition
        assert not post_condition

    def test_exceeding_number_of_guesses_ends_turn(self, blue_player_turn_state):
        # when
        blue_player_turn_state.guess(2)
        blue_player_turn_state.guess(7)
        game_info = blue_player_turn_state.get_info()

        # then
        assert game_info["conditions"][-1]["value"] == Condition.RED_SPY

    def test_guessing_opposite_color_ends_turn(self, blue_player_turn_state):
        # when
        blue_player_turn_state.guess(1)
        game_info = blue_player_turn_state.get_info()

        # then
        assert game_info["conditions"][-1]["value"] == Condition.RED_SPY

    def test_guessing_opposite_color_loses_game(self, backend, blue_player_turn_state):
        # given
        backend.add_guess(1)
        backend.add_guess(8)  # only a single red word is left

        # when
        blue_player_turn_state.guess(3)
        game_info = blue_player_turn_state.get_info()

        # then
        assert game_info["conditions"][-1]["value"] == Condition.RED_WINS

    def test_guessing_neutral_color_ends_turn(self, blue_player_turn_state):
        # when
        blue_player_turn_state.guess(5)
        game_info = blue_player_turn_state.get_info()

        # then
        assert game_info["conditions"][-1]["value"] == Condition.RED_SPY

    def test_guessing_final_word_wins_game(self, backend, blue_player_turn_state):
        # given
        backend.add_hint("myhint", 1, Color.BLUE)
        backend.add_guess(2)
        backend.add_guess(7)  # only a single blue word is left

        # when
        blue_player_turn_state.guess(4)
        game_info = blue_player_turn_state.get_info()

        # then
        assert game_info["conditions"][-1]["value"] == Condition.BLUE_WINS

    def test_guessing_assassin_loses_game(self, blue_player_turn_state):
        # when
        blue_player_turn_state.guess(6)
        game_info = blue_player_turn_state.get_info()

        # then
        assert game_info["conditions"][-1]["value"] == Condition.RED_WINS

    def test_end_turn(self, blue_player_turn_state):
        # when
        blue_player_turn_state.end_turn()
        value = blue_player_turn_state.get_info()

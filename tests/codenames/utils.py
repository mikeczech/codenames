from codenames.game import (
    Color,
    Role,
    Condition,
)

from codenames import models


def create_default_game(db):
    """ Adds a simple game to the database. """
    games = [models.Game(id=42, name="mygame")]
    active_words = [
        models.ActiveWord(game_id=42, word_id=1, color=Color.RED.value),
        models.ActiveWord(game_id=42, word_id=2, color=Color.BLUE.value),
        models.ActiveWord(game_id=42, word_id=3, color=Color.RED.value),
        models.ActiveWord(game_id=42, word_id=4, color=Color.BLUE.value),
        models.ActiveWord(game_id=42, word_id=5, color=Color.NEUTRAL.value),
        models.ActiveWord(game_id=42, word_id=6, color=Color.ASSASSIN.value),
        models.ActiveWord(game_id=42, word_id=7, color=Color.BLUE.value),
        models.ActiveWord(game_id=42, word_id=8, color=Color.RED.value),
    ]
    conditions = [models.Condition(game_id=42, condition=Condition.NOT_STARTED.value)]
    hints = [models.Hint(game_id=42)]

    db.add_all(games)
    db.add_all(active_words)
    db.add_all(conditions)
    db.add_all(hints)
    db.commit()


def add_players(db):
    players = [
        models.Player(
            game_id=42, session_id="A23", color=Color.RED.value, role=Role.PLAYER.value
        ),
        models.Player(
            game_id=42,
            session_id="A22",
            color=Color.RED.value,
            role=Role.SPYMASTER.value,
        ),
        models.Player(
            game_id=42, session_id="A21", color=Color.BLUE.value, role=Role.PLAYER.value
        ),
        models.Player(
            game_id=42,
            session_id="A100",
            color=Color.BLUE.value,
            role=Role.SPYMASTER.value,
        ),
    ]
    db.add_all(players)
    db.commit()

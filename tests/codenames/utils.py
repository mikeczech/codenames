from codenames.game import (
    Color,
    Role,
    Condition,
)


def create_default_game(db_con):
    """ Adds a simple game to the database. """
    active_words = [(42, 1, Color.RED.value), (42, 2, Color.BLUE.value)]
    turns = [(42, Condition.NOT_STARTED.value)]
    db_con.executemany(
        """
        INSERT INTO active_words (game_id, word_id, color) VALUES (?, ?, ?)
    """,
        active_words,
    )
    db_con.executemany(
        """
        INSERT INTO turns (game_id, condition, created_at) VALUES (?, ?, strftime('%s', 'now'))
    """,
        turns,
    )


def add_players(db_con):
    players = [
        (42, "A23", Color.RED.value, Role.PLAYER.value, False),
        (42, "A22", Color.RED.value, Role.SPYMASTER.value, True),
        (42, "A21", Color.BLUE.value, Role.PLAYER.value, False),
        (42, "A100", Color.BLUE.value, Role.SPYMASTER.value, False),
    ]
    db_con.executemany(
        """
        INSERT INTO players (game_id, session_id, color, role, is_admin) VALUES (?, ?, ?, ?, ?)
    """,
        players,
    )

from codenames.game import (
    Color,
    Role,
    Condition,
)


def create_default_game(db_con):
    """ Adds a simple game to the database. """
    active_words = [
        (42, 1, Color.RED.value),
        (42, 2, Color.BLUE.value),
        (42, 3, Color.RED.value),
        (42, 4, Color.BLUE.value),
        (42, 5, Color.NEUTRAL.value),
        (42, 6, Color.ASSASSIN.value),
        (42, 7, Color.BLUE.value),
        (42, 8, Color.RED.value),
    ]
    turns = [(42, None, Condition.NOT_STARTED.value)]
    hints = [(42, None, None, None)]
    db_con.executemany(
        """
        INSERT INTO 
            active_words (game_id, word_id, color)
        VALUES (?, ?, ?)
    """,
        active_words,
    )
    db_con.executemany(
        """
        INSERT INTO
            turns (game_id, hint_id, condition, created_at)
        VALUES (?, ?, ?, strftime('%s', 'now'))
    """,
        turns,
    )
    db_con.executemany(
        """
        INSERT INTO
            hints (game_id, hint, num, color, created_at)
        VALUES (?, ?, ?, ?, strftime('%s', 'now'))
    """,
        hints,
    )
    db_con.commit()


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
    db_con.commit()

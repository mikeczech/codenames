import random

from flask import Blueprint
from flask import render_template
from flask import redirect
from flask import request
from flask import url_for
from flask import jsonify

from codenames.db import get_db
from codenames.errors import InvalidUsage

bp = Blueprint("api", __name__, url_prefix="/api")

NUM_RED_WORDS = 9
NUM_BLUE_WORDS = 9
NUM_NEUTRAL_WORDS = 9
NUM_ASSASSIN_WORDS = 1
NUM_WORDS_PER_GAME = (
    NUM_RED_WORDS + NUM_BLUE_WORDS + NUM_NEUTRAL_WORDS + NUM_ASSASSIN_WORDS
)


@bp.route("/create", methods=("POST",))
def create():
    game_id = request.json["gameId"]
    db = get_db()
    error = None

    if not game_id:
        error = "Invalid game id"
    elif (
        db.execute("SELECT name from games WHERE name = ?", (game_id,)).fetchone()
        is not None
    ):
        error = f"Game '{game_id}' already exists"

    if error is not None:
        raise InvalidUsage(f"An error occurred: {error}", status_code=400)

    db.execute("INSERT INTO games (name) VALUES (?)", (game_id,))

    game = db.execute("SELECT id from games WHERE name = ?", (game_id,)).fetchone()
    words = db.execute(
        "SELECT id, word from words ORDER BY RANDOM() LIMIT ?", (NUM_WORDS_PER_GAME,)
    ).fetchall()

    colors = (
        ["red"] * NUM_RED_WORDS
        + ["blue"] * NUM_BLUE_WORDS
        + ["neutral"] * NUM_NEUTRAL_WORDS
        + ["assassin"] * NUM_ASSASSIN_WORDS
    )
    random.shuffle(colors)
    active_words = [
        (game["id"], word["id"], color) for word, color in zip(words, colors)
    ]

    db.executemany(
        "INSERT INTO active_words (game_id, word_id, color) VALUES (?, ?, ?);",
        active_words,
    )

    db.commit()

    return jsonify(success=True)


@bp.route("/state", methods=("GET",))
def state():
    game_id = request.args.get("gameId")
    db = get_db()
    error = None

    if not game_id:
        raise InvalidUsage("No game id specified")

    active_words = db.execute(
        """
        SELECT word, color
        FROM active_words
        JOIN words
        ON words.id = active_words.word_id
        JOIN (SELECT id FROM games where name = ?) game
        ON game.id = active_words.game_id
    """,
        (game_id,),
    ).fetchall()

    if active_words is None or len(active_words) == 0:
        raise InvalidUsage(
            f"There is no game state associated with game {game_id}", status_code=400
        )

    resp = [{"word": w["word"], "color": w["color"]} for w in active_words]
    return jsonify(resp)


@bp.route("/join", methods=("POST",))
def join():
    username = request.json["username"]
    kind = request.json["kind"]
    game_id = request.json["gameId"]

    if (
        db.execute("SELECT game_id FROM games WHERE game_id = ?", (game_id,)).fetchone()
        is None
    ):
        raise InvalidUsage("Game with id {game_id} does not exist")

    active_player = db.execute(
        "SELECT username FROM players WHERE game_id = ? and kind = ?", (game_id, kind)
    ).fetchone()
    if active_player is not None:
        raise InvalidUsage("User {active_player['username']} is already of kind {kind}")

    db.execute("INSERT INTO players (game_id, username, kind) VALUES (?, ?, ?);")
    db.commit()

    return jsonify(success=True)

from flask import Blueprint

from flask import render_template
from flask import redirect
from flask import request
from flask import url_for
from flask import jsonify

from codenames.db import get_db
from codenames.errors import InvalidUsage

bp = Blueprint("api", __name__, url_prefix="/api")

@bp.route("/create", methods=("POST", ))
def create():
    game_id = request.form["game-id"]
    db = get_db()
    error = None

    if not game_id:
        error = "Invalid game id"
    elif db.execute("SELECT name from games WHERE name = ?", (game_id,)).fetchone() is not None:
        error = f"Game {game_id} already exists"

    if error is not None:
        raise InvalidUsage(f"An error occurred: {error}", status_code = 400)

    db.execute(
        "INSERT INTO games (name) VALUES (?)",
        (game_id,)
    )

    db.commit()
    return jsonify(success=True)


@bp.route("/game", methods=("GET",))
def game():
    game_id = request.args.get("game-id")
    db = get_db()
    error = None

    if not game_id:
        error = "Invalid game id"

    game = db.execute("SELECT name from games WHERE name = ?", (game_id,)).fetchone()
    if game is None:
        error = f"Game {game_id} does not exist"

    if error is not None:
        raise InvalidUsage(f"An error occurred: {error}", status_code = 400)

    return jsonify(name=game["name"])

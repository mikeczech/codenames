from flask import Blueprint

from flask import render_template
from flask import redirect
from flask import request
from flask import url_for
from flask import flash

from codenames.db import get_db
from codenames.errors import InvalidUsage

bp = Blueprint("api", __name__, url_prefix="/api")

@bp.route("/create", methods=("GET", "POST"))
def create():
    if request.method == "POST":
        game_id = request.form["game-id"]
        db = get_db()
        error = None

        if not game_id:
            error = "Invalid game id"
        elif db.execute("SELECT name from games WHERE name = ?", (game_id,)).fetchone() is not None:
            error = f"Game {game_id} already exists"

        if error is None:
            db.execute(
                "INSERT INTO games (name) VALUES (?)",
                (game_id,)
            )
            db.commit()
        else:
            raise InvalidUsage(f"An error occurred: {error}", status_code = 400)

    return render_template("create_game.html")

@bp.route("/<game_id>")
def game(game_id):
    return render_template("game.html", game_id=game_id)

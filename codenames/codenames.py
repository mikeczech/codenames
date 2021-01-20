from flask import Blueprint
from flask import render_template
from flask import redirect
from flask import request
from flask import url_for
from flask import flash

bp = Blueprint("codenames", __name__)

@bp.route("/", methods=("GET", "POST"))
def index():
    if request.method == "POST":
        game_id = request.form["game-id"]
        error = None
        if not game_id:
            error = "Invalid game id"
        if error is None:
            return redirect(url_for("codenames.game", game_id=game_id))
        flash(error)

    return render_template("create_game.html")

@bp.route("/<game_id>")
def game(game_id):
    return render_template("game.html", game_id=game_id)

"""create initial tables

Revision ID: 6fae36685ece
Revises: 
Create Date: 2021-09-23 18:52:38.312056

"""
import os
import csv

from alembic import op
import sqlalchemy as sa

from codenames import models


# revision identifiers, used by Alembic.
revision = '6fae36685ece'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # add tables
    op.create_table(
      "games",
      sa.Column('id', sa.Integer, primary_key=True),
      sa.Column('name', sa.String(50))
    )

    op.create_table(
      "words",
      sa.Column('id', sa.Integer, primary_key=True),
      sa.Column('value', sa.String(50))
    )

    op.create_table(
      "players",
      sa.Column('id', sa.Integer, primary_key=True),
      sa.Column('name', sa.String(50)),
      sa.Column('game_id', sa.Integer),
      sa.Column('session_id', sa.String(50)),
      sa.Column('color', sa.Integer),
      sa.Column('role', sa.Integer),
    )

    op.create_table(
      "active_words",
      sa.Column('id', sa.Integer, primary_key=True),
      sa.Column('game_id', sa.Integer),
      sa.Column('word_id', sa.Integer),
      sa.Column('color', sa.Integer),
    )

    op.create_table(
      "conditions",
      sa.Column('id', sa.Integer, primary_key=True),
      sa.Column('game_id', sa.Integer),
      sa.Column('hint_id', sa.Integer),
      sa.Column('condition', sa.Integer),
      sa.Column('created_at', sa.Integer),
    )

    op.create_table(
      "moves",
      sa.Column('id', sa.Integer, primary_key=True),
      sa.Column('game_id', sa.Integer),
      sa.Column('active_word_id', sa.Integer),
      sa.Column('selected_at', sa.Integer),
    )

    op.create_table(
      "hints",
      sa.Column('id', sa.Integer, primary_key=True),
      sa.Column('game_id', sa.Integer),
      sa.Column('hint', sa.String(100)),
      sa.Column('num', sa.Integer),
      sa.Column('color', sa.Integer),
      sa.Column('created_at', sa.Integer),
    )

    # add words
    this_dir, _ = os.path.split(__file__)
    bind = op.get_bind()
    session = sa.orm.Session(bind=bind)
    words_path = os.path.join(this_dir, "..", "..", "codenames", "data", "words.csv")
    with open(words_path, "r") as f:
        rows = csv.DictReader(f)
        for r in rows:
            session.add(models.Word(id=r["id"], value=r["word"]))
    session.commit()


def downgrade():
    op.drop_table("games")
    op.drop_table("words")
    op.drop_table("players")
    op.drop_table("active_words")
    op.drop_table("conditions")
    op.drop_table("moves")
    op.drop_table("hints")

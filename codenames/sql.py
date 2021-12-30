from typing import Dict, Union, Any, List, Tuple, Optional
from itertools import chain
import random
import time

from codenames.game import (
    GameBackend,
    Game,
    Color,
    Role,
    Condition,
    GameAlreadyExistsException,
    Word,
)

from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import func
from sqlalchemy import desc
from codenames import models, schemas


class SQLAlchemyGameBackend(GameBackend):
    def __init__(self, game_id: int, db: Session):
        self._game_id = game_id
        self._db = db

    @property
    def game_id(self) -> int:
        return self._game_id

    def load(self) -> Dict[str, Any]:
        game = self._db.query(models.Game).filter_by(id=self._game_id).first()

        return {
            "words": {
                w.id: Word(
                    id=w.id,
                    value=w.word.value,
                    color=Color(w.color),
                    selected_at=w.move.selected_at if w.move else None,
                )
                for w in game.active_words
            },
            "hints": [
                {
                    "id": h.id,
                    "word": h.hint,
                    "num": h.num,
                    "color": Color(h.color) if h.color else None,
                }
                for h in game.hints
            ],
            "conditions": [
                {"value": Condition(t.condition), "hint_id": t.hint_id}
                for t in game.conditions
            ],
            "players": [
                {
                    "session_id": p.session_id,
                    "color": Color(p.color),
                    "role": Role(p.role),
                }
                for p in game.players
            ],
        }

    def read_active_words(self):
        return (
            self._db.query(models.ActiveWord)
            .filter(models.ActiveWord.game_id == self._game_id)
            .all()
        )

    def add_guess(self, word_id: int) -> None:
        self._db.add(
            models.Move(
                game_id=self._game_id,
                active_word_id=word_id,
                selected_at=int(time.time()),
            )
        )

    def read_conditions(self):
        return (
            self._db.query(models.Condition)
            .filter(models.Condition.game_id == self._game_id)
            .all()
        )

    def add_hint(self, word: str, num: int, color: Color) -> int:
        hint = models.Hint(
            game_id=self._game_id,
            hint=word,
            num=num,
            color=color.value,
            created_at=int(time.time()),
        )
        self._db.add(hint)
        self._db.flush()
        self._db.refresh(hint)
        return hint.id

    def read_hints(self):
        return (
            self._db.query(models.Hint)
            .filter(models.Hint.game_id == self._game_id)
            .all()
        )

    def add_condition(
        self, condition: Condition, hint_id: Optional[int] = None
    ) -> None:
        self._db.add(
            models.Condition(
                game_id=self._game_id,
                hint_id=hint_id,
                condition=condition.value,
                created_at=int(time.time()),
            )
        )

    def is_occupied(self, color: Color, role: Role) -> bool:
        player_count = (
            self._db.query(models.Player)
            .filter_by(game_id=self._game_id, color=color.value, role=role.value)
            .count()
        )
        return player_count > 0

    def add_player(self, session_id: str, color: Color, role: Role) -> None:
        self._db.add(
            models.Player(
                game_id=self._game_id,
                session_id=session_id,
                color=color.value,
                role=role.value,
            )
        )

    def read_players(self):
        return (
            self._db.query(models.Player)
            .filter(models.Player.game_id == self._game_id)
            .all()
        )

    def has_joined(self, session_id: str) -> bool:
        player_count = (
            self._db.query(models.Player)
            .filter_by(game_id=self._game_id, session_id=session_id)
            .count()
        )
        return player_count > 0

    def remove_player(self, session_id: str) -> None:
        self._db.query(models.Player).filter_by(
            game_id=self._game_id, session_id=session_id
        ).delete()

    def get_active_session_id(self) -> str:
        game_condition = Condition(
            self._db.query(models.Condition)
            .filter_by(game_id=self._game_id)
            .order_by(desc(models.Condition.id))
            .first()
            .condition
        )

        active_player = (
            self._db.query(models.Player)
            .filter_by(
                game_id=self._game_id,
                color=game_condition.color.value,
                role=game_condition.role.value,
            )
            .first()
        )

        if not active_player:
            raise Exception("Could not determine active player (maybe there is none?)")

        return active_player.session_id

    def commit(self) -> None:
        self._db.commit()


class SQLAlchemyGameManager:
    def __init__(
        self,
        db: Session,
        num_blue: int = 9,
        num_red: int = 9,
        num_neutral: int = 9,
        num_assassin: int = 1,
    ):
        self._db = db
        self._word_color_counts = {
            Color.BLUE.value: num_blue,
            Color.RED.value: num_red,
            Color.NEUTRAL.value: num_neutral,
            Color.ASSASSIN.value: num_assassin,
        }

    def exists(self, name: str) -> bool:
        res = self._db.query(models.Game).filter(models.Game.name == name).first()
        if res:
            return True
        return False

    def create_random(self, name: str, session_id: str, random_seed: int = None) -> Game:
        random.seed(random_seed)

        game = self._create_game(name, session_id)
        random_words = self._get_random_words()

        active_words = [
            models.ActiveWord(game_id=game.id, word_id=w.id, color=w.color)
            for w in random_words
        ]
        self._db.add_all(active_words)
        self._db.add(
            models.Condition(game_id=game.id, condition=Condition.NOT_STARTED.value)
        )
        self._db.add(
            models.Hint(game_id=game.id, hint=None, num=None, color=None, created_at=0)
        )

        self._db.commit()
        return game

    def get(self, name: str) -> Optional[Game]:
        return None

    def _create_game(self, name: str, session_id: str) -> Game:
        if self.exists(name):
            raise GameAlreadyExistsException()

        self._db.add(models.Game(name=name))
        self._db.commit()
        game = self._db.query(models.Game).filter(models.Game.name == name).first()
        return Game(session_id, SQLAlchemyGameBackend(game.id, self._db))

    def _get_random_words(self) -> List[Word]:
        all_words = self._db.query(models.Word).all()
        words = random.sample(all_words, sum(self._word_color_counts.values()))
        random_colors = self._get_random_colors()
        return [Word(w.id, w.value, c, None) for w, c in zip(words, random_colors)]

    def _get_random_colors(self) -> List[str]:
        ret = list(
            chain(
                *[[color] * count for color, count in self._word_color_counts.items()]
            )
        )
        random.shuffle(ret)
        return ret

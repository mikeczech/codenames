from typing import List, Optional

from pydantic import BaseModel


class Game(BaseModel):
    id: int
    name: str


class Player(BaseModel):
    game_id: int
    session_id: str
    color: int
    role: int


class Word(BaseModel):
    id: int
    value: str


class ActiveWord(BaseModel):
    game_id: int
    word_id: int
    color: int


class Condition(BaseModel):
    hint_id: int
    game_id: int
    condition: int
    created_at: int


class Move(BaseModel):
    id: int
    game_id: int
    word_id: int
    selected_at: int


class Hint(BaseModel):
    id: int
    game_id: int
    hint: str
    num: int
    color: int
    created_at: int

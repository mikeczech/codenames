from typing import List, Optional

from pydantic import BaseModel


class Player(BaseModel):
    game_id: int
    session_id: str
    color: int
    role: int

    class Config:
        orm_mode = True


class Word(BaseModel):
    id: int
    value: str

    class Config:
        orm_mode = True


class ActiveWord(BaseModel):
    game_id: int
    word_id: int
    color: int

    word: Word

    class Config:
        orm_mode = True


class Condition(BaseModel):
    hint_id: Optional[int]
    game_id: int
    condition: int
    created_at: Optional[int]

    class Config:
        orm_mode = True


class Move(BaseModel):
    id: int
    game_id: int
    word_id: int
    selected_at: int

    class Config:
        orm_mode = True


class Hint(BaseModel):
    id: int
    game_id: int
    hint: Optional[str]
    num: Optional[int]
    color: Optional[int]
    created_at: int

    class Config:
        orm_mode = True


class Game(BaseModel):
    id: int
    name: str

    active_words: List[ActiveWord] = []
    moves: List[Move] = []
    conditions: List[Condition] = []
    hints: List[Hint] = []
    players: List[Player] = []

    class Config:
        orm_mode = True

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"))
    session_id = Column(String)
    color = Column(Integer)
    role = Column(Integer)


class Word(Base):
    __tablename__ = "words"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    value = Column(String)


class ActiveWord(Base):
    __tablename__ = "active_words"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"))
    word_id = Column(Integer, ForeignKey("words.id"))
    color = Column(Integer)


class Condition(Base):
    __tablename__ = "conditions"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"))
    condition = Column(Integer)
    created_at = Column(Integer)


class Move(Base):
    __tablename__ = "moves"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"))
    word_id = Column(Integer, ForeignKey("words.id"))
    selected_at = Column(Integer)


class Hint(Base):
    __tablename__ = "hints"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"))
    hint = Column(String)
    num = Column(Integer)
    color = Column(Integer)
    created_at = Column(Integer)

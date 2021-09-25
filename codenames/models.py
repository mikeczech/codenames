from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)

    active_words = relationship("ActiveWord", back_populates="game")
    moves = relationship("Move", back_populates="game")
    conditions = relationship("Condition", back_populates="game")
    hints = relationship("Hint", back_populates="game")
    players = relationship("Player", back_populates="game")


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"))
    game = relationship("Game", back_populates="players")

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
    game = relationship("Game", back_populates="active_words")

    word_id = Column(Integer, ForeignKey("words.id"))
    word = relationship("Word")

    move = relationship("Move", back_populates="active_word", uselist=False)

    color = Column(Integer)


class Condition(Base):
    __tablename__ = "conditions"

    id = Column(Integer, primary_key=True, index=True)

    game_id = Column(Integer, ForeignKey("games.id"))
    game = relationship("Game", back_populates="conditions")

    hint_id = Column(Integer, ForeignKey("hints.id"))
    hint = relationship("Hint", back_populates="conditions")

    condition = Column(Integer)
    created_at = Column(Integer)


class Move(Base):
    __tablename__ = "moves"

    id = Column(Integer, primary_key=True, index=True)

    game_id = Column(Integer, ForeignKey("games.id"))
    game = relationship("Game", back_populates="moves")

    active_word_id = Column(Integer, ForeignKey("active_words.id"))
    active_word = relationship("ActiveWord", back_populates="move")

    selected_at = Column(Integer)


class Hint(Base):
    __tablename__ = "hints"

    id = Column(Integer, primary_key=True, index=True)

    game_id = Column(Integer, ForeignKey("games.id"))
    game = relationship("Game", back_populates="hints")

    conditions = relationship("Condition", back_populates="hint")

    hint = Column(String)
    num = Column(Integer)
    color = Column(Integer)
    created_at = Column(Integer)

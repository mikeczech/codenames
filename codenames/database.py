from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


SQLALCHEMY_DATABASE_URL = "sqlite:///instance/codenames.sqlite"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

from codenames import models
from codenames.sql import SQLAlchemyGameManager

m = SQLAlchemyGameManager(db=SessionLocal())
m.create_random("foo", "A42")

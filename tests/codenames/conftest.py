from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from alembic.command import upgrade as alembic_upgrade
from alembic.config import Config as AlembicConfig


import pytest


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", echo=True)
    session_factory = sessionmaker(bind=engine)
    print("\n----- CREATE TEST DB CONNECTION POOL\n")

    _db = {
        "engine": engine,
        "session_factory": session_factory,
    }
    alembic_config = AlembicConfig("alembic.ini")
    alembic_config.set_main_option("sqlalchemy.url", "sqlite:///:memory:")
    with engine.begin() as connection:
        alembic_config.attributes["connection"] = connection
        alembic_upgrade(alembic_config, "head")
    print("\n----- RUN ALEMBIC MIGRATION\n")
    yield _db["session_factory"]()
    print("\n----- CREATE TEST DB INSTANCE POOL\n")

    engine.dispose()
    print("\n----- RELEASE TEST DB CONNECTION POOL\n")

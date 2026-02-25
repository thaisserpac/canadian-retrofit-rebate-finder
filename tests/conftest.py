import pytest
from unittest.mock import patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.database import Base, get_db

# Import all models so Base.metadata knows about every table
import app.models  # noqa: F401

from app.data.seed_rebates import seed_database


@pytest.fixture(scope="session")
def engine():
    eng = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=eng)
    # Seed once for the whole test session
    TestSession = sessionmaker(bind=eng)
    session = TestSession()
    seed_database(session)
    session.close()
    return eng


@pytest.fixture()
def db(engine):
    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db):
    def override_get_db():
        yield db

    from app.main import app

    app.dependency_overrides[get_db] = override_get_db

    with patch("app.main.init_db"), patch("app.main.seed_database"):
        with TestClient(app) as c:
            yield c

    app.dependency_overrides.clear()

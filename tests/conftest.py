import os

import pytest

from app import create_app
from app.db import Base, get_engine, init_app, get_session


@pytest.fixture()
def app(tmp_path):
    db_path = tmp_path / "test.db"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    app = create_app()
    app.config["DATABASE_URL"] = os.environ["DATABASE_URL"]
    init_app(app)

    engine = get_engine(app.config["DATABASE_URL"])
    Base.metadata.create_all(bind=engine)

    yield app

    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def session(app):
    with get_session(app) as session:
        yield session

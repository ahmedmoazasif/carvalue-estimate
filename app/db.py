from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    pass


SessionLocal = sessionmaker(class_=Session, autoflush=False, autocommit=False)


def get_engine(database_url: str):
    return create_engine(database_url, future=True)


def init_app(app) -> None:
    engine = get_engine(app.config["DATABASE_URL"])
    app.extensions["engine"] = engine


@contextmanager
def get_session(app) -> Generator[Session, None, None]:
    engine = app.extensions["engine"]
    session = SessionLocal(bind=engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

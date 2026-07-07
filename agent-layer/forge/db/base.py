"""SQLAlchemy declarative base and session factory helpers."""

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    """Declarative base shared by all Forge ORM models."""


def create_db_engine(database_url: str) -> Engine:
    # pool_pre_ping so long-idle connections (overnight dev machines,
    # Postgres restarts) are transparently replaced instead of erroring.
    return create_engine(database_url, pool_pre_ping=True)


def create_session_factory(engine: Engine) -> sessionmaker:
    # expire_on_commit=False: gateway code returns ORM-derived data after
    # commit; we don't want lazy refresh round-trips on detached objects.
    return sessionmaker(bind=engine, expire_on_commit=False)

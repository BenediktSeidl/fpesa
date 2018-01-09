"""
--------
postgres
--------
"""
from functools import wraps

from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSONB

from fpesa.helper import get_engine

Base = declarative_base()

Session = sessionmaker(bind=get_engine())
# TODO: move into function and global variable?!


class Message(Base):
    """
    Wraps a JSON Message
    """
    __tablename__ = 'message'
    id = Column(Integer, primary_key=True)
    inserted = Column(DateTime, server_default=func.now())
    message = Column(JSONB)

    def __init__(self, message):
        self.message = message


def with_session(f):
    """
    Decorator that injects a Session object as the first paramter.

    Commits and closes the session of no exception occures. When a exception
    occures, the session is rolled back.
    """
    @wraps(f)
    def wrapper(*args, **kwds):
        session = Session()
        try:
            result = f(session, *args, **kwds)
            session.commit()
            return result
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    return wrapper


@with_session
def create_all(session):
    """
    create all tables

    :param sqlalchemy.orm.session.Session session: session object injected via
        :py:func:`fpesa.postgres.with_session` decorator.
    """
    Base.metadata.create_all(session.get_bind())

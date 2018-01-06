from functools import wraps

from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSONB

from fpesa.helper import get_engine

Base = declarative_base()

Session = sessionmaker(bind=get_engine())


class Message(Base):
    __tablename__ = 'message'
    id = Column(Integer, primary_key=True)
    inserted = Column(DateTime, server_default=func.now())
    message = Column(JSONB)

    def __init__(self, message):
        self.message = message


def with_session(f):
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
    Base.metadata.create_all(session.get_bind())

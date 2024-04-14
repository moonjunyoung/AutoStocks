from typing import Callable, ContextManager
from sqlalchemy import create_engine, Column, Integer, String, Sequence
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine = create_engine("sqlite:///develop.db", echo=True)
Base = declarative_base()
Session = sessionmaker(bind=engine)


def get_session():
    try:
        db_session = Session()
        yield db_session
    finally:
        db_session.close()


class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    platform = Column(String)
    platform_id = Column(String)

    def __init__(self, id, platform, platform_id):
        self.id = id
        self.platform = platform
        self.platform_id = platform_id


Base.metadata.create_all(engine)

from sqlmodel import SQLModel
from sqlmodel import create_engine
from models import Link


engine = create_engine("sqlite:///database.db", echo=True)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_engine():
    return engine

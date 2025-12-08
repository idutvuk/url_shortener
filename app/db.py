from sqlalchemy import Engine
from sqlmodel import SQLModel, create_engine

engine: Engine = create_engine("sqlite:///database.db")


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_engine() -> Engine:
    return engine

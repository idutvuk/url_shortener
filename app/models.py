from sqlmodel import Field, SQLModel


class Link(SQLModel, table=True):
    id: int | None = Field(index=True, default=None, primary_key=True)
    nickname: str
    url: str
    author: str | None

from fastapi import FastAPI, Depends, HTTPException
import uvicorn
from sqlmodel import Session, select, col
from starlette.responses import RedirectResponse

from db import create_db_and_tables, get_engine
from contextlib import asynccontextmanager

from models import Link

from random import choice


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield
    # something on exit


app = FastAPI(lifespan=lifespan)


@app.get("/links/")
async def get_all_links(engine=Depends(get_engine)):
    with Session(engine) as s:
        return s.exec(select(Link)).all()


@app.post("/links/", status_code=201)
async def add_link(link: Link, engine=Depends(get_engine)):
    with Session(engine) as s:
        statement = select(Link.url).where(Link.nickname == link.nickname)
        if s.exec(statement).first():
            return HTTPException(409)

        s.add(link)
        s.commit()
        s.refresh(link)
        return link


@app.get("/{nickname}", status_code=303)
async def redirect(nickname: str, engine=Depends(get_engine)):
    with Session(engine) as s:
        statement = select(Link.url).where(Link.nickname == nickname)
        url = s.exec(statement).first()
        if not url:
            return HTTPException(404)
        return RedirectResponse(url=str(url))


@app.delete("/{nickname}")
async def delete_record(nickname: str, engine=Depends(get_engine)):
    with Session(engine) as s:
        statement = select(Link).where(Link.nickname == nickname)
        obj = s.exec(statement).first()
        if not obj:
            return HTTPException(404)
        s.delete(obj)
        s.commit()


# @app.post("/{url}")
# async def create_fast_link(url: str):
#     FAST_LINK_LENGTH = 4
#     link = Link(link=generate_fast_link(FAST_LINK_LENGTH), url=url)
#     await add_link(link)


# def generate_fast_link(length) -> str:
#     alphabet = list(map(chr, range(ord('a'), ord('z') + 1)))
#     link = []
#     for c in range(length):
#         link.append(choice[alphabet])
#     return link

if __name__ == "__main__":
    # todo add validating for https:// prefix
    uvicorn.run("server:app", reload=True)

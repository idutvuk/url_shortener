from fastapi import FastAPI, Depends, HTTPException
import uvicorn
from sqlmodel import Session, select, col
from db import create_db_and_tables, get_engine
from contextlib import asynccontextmanager

from models import Link


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
        s.add(link)
        s.commit()
        s.refresh(link)
        return link


@app.get("/{nickname}")
async def redirect(nickname: str, engine=Depends(get_engine)):
    with Session(engine) as s:
        statement = select(Link.url).where(Link.nickname == nickname)
        url = s.exec(statement).first()
        if not url:
            return HTTPException(404)
        return url


if __name__ == "__main__":
    uvicorn.run("server:app", reload=True)

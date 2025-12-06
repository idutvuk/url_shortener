from fastapi import FastAPI, Depends, HTTPException, APIRouter
import uvicorn
from sqlmodel import Session, select, col
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBasicCredentials, HTTPBasic

from db import create_db_and_tables, get_engine
from contextlib import asynccontextmanager

from models import Link

from loguru import logger

from random import choice

import string

from dotenv import load_dotenv

import os


security = HTTPBasic()


def auth(creds: HTTPBasicCredentials = Depends(security)) -> str:
    check_username = creds.username == os.getenv("admin")
    check_password = creds.password == os.getenv("password")
    if check_username and check_password:
        return creds.username
    raise HTTPException(401)


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_dotenv()  # todo replace dotenv with something more nice
    create_db_and_tables()
    yield
    # something on exit


app = FastAPI(lifespan=lifespan)


@app.get("/{nickname}", status_code=303)
async def redirect(nickname: str, engine=Depends(get_engine)):
    with Session(engine) as s:
        statement = select(Link.url).where(Link.nickname == nickname)
        url = s.exec(statement).first()
        if not url:
            return HTTPException(404)
        return RedirectResponse(url=str(url))


# admin zone


@app.get("/links/")
async def get_all_links(engine=Depends(get_engine), user=Depends(auth)):
    with Session(engine) as s:
        return s.exec(select(Link)).all()


def add_link_to_db(link: Link, engine) -> Link:
    link.url = validated_url(link.url)
    with Session(engine) as s:
        statement = select(Link.url).where(Link.nickname == link.nickname)
        if s.exec(statement).first():
            return HTTPException(409)

        s.add(link)
        s.commit()
        s.refresh(link)
        return link


@app.post("/links/", status_code=201)
async def add_link(
    link: Link, 
    engine=Depends(get_engine), 
    user=Depends(auth)
    ):
    return add_link_to_db(link, engine)


@app.delete("/{nickname}")
async def delete_record(
    nickname: str, 
    engine=Depends(get_engine), 
    user=Depends(auth)
    ):
    with Session(engine) as s:
        statement = select(Link).where(Link.nickname == nickname)
        obj = s.exec(statement).first()
        if not obj:
            return HTTPException(404)
        s.delete(obj)
        s.commit()


@app.post("/{url}", status_code=201)
async def create_fast_link(
    url: str, 
    engine=Depends(get_engine), 
    user=Depends(auth)
    ):
    FAST_LINK_LENGTH = 4
    link = Link(nickname=generate_fast_link(FAST_LINK_LENGTH), url=url)
    logger.info(f"Created link for {url} - {link.nickname}")
    add_link_to_db(link, engine)
    return os.getenv("BASE_URL")+"/"+link.nickname

def generate_fast_link(length) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(choice(alphabet) for _ in range(length))

def validated_url(url) -> str:
    # too simple but its okay i guess
    if not url.startswith("https://"):
        url = "https://"+url
    return url

if __name__ == "__main__":
    uvicorn.run(
        "server:app", 
        reload=os.getenv("DEBUG_MODE") in ("True", "true" "1",1, True), 
        port=int(os.getenv("PORT"))
        )
    

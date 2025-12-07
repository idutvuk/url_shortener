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


load_dotenv()

DEBUG_MODE = os.getenv("DEBUG_MODE") in ("True", "true" "1",1, True)
BASE_URL = os.getenv("BASE_URL")
PREFIX = os.getenv("PREFIX")

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


app = FastAPI(lifespan=lifespan) if DEBUG_MODE else FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
r = APIRouter(prefix=PREFIX)



@r.get("/{nickname}", status_code=303)
async def redirect(nickname: str, engine=Depends(get_engine)):
    with Session(engine) as s:
        statement = select(Link.url).where(Link.nickname == nickname)
        url = s.exec(statement).first()
        if not url:
            return HTTPException(404)
        return RedirectResponse(url=str(url))


# admin zone


@r.get("/links/")
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


@r.post("/links/", status_code=201)
async def add_link(
    nickname: str, 
    url: str,
    engine=Depends(get_engine), 
    user=Depends(auth)
    ):
    return add_link_to_db(Link(nickname=nickname, url=url), engine)


@r.delete("/{nickname}")
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
#

@r.post("/{url:path}", status_code=201)
async def create_fast_link(
    url: str, 
    engine=Depends(get_engine), 
    # user=Depends(auth) # lets say this pointer is public
    ):
    FAST_LINK_LENGTH = 4
    with Session(engine) as s:
        nicknames = s.exec(select(Link.nickname)).all()
        while (fast_link := generate_fast_link(FAST_LINK_LENGTH)) in nicknames:
            pass
    
    link = Link(nickname=fast_link, url=url)
    logger.info(f"Created link for {url} - {link.nickname}")
    add_link_to_db(link, engine)
    return BASE_URL+PREFIX+"/"+link.nickname

def generate_fast_link(length) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(choice(alphabet) for _ in range(length))

def validated_url(url) -> str:
    # too simple but its okay i guess
    if not url.startswith("https://"): # todo add check for http://
        url = "https://"+url
    return url


app.include_router(r)


if __name__ == "__main__":
    uvicorn.run(
        "server:app", 
        reload=DEBUG_MODE, 
        port=int(os.getenv("PORT"))
        )
    

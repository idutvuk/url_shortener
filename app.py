from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from pathlib import Path
import os
import json

app = FastAPI(title="URL Shortener")

SHORTENER_FILE = "shortened_urls.json"

@app.get("/api/urls")
def load_urls():
    if not os.path.exists(SHORTENER_FILE):
        return {}
    try:
        with open(SHORTENER_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def save_urls(urls):
    with open(SHORTENER_FILE, 'w') as f:
        json.dump(urls, f, indent=2)



class URLCreate(BaseModel):
    url: str
    short_code: str

class URLResponse(BaseModel):
    url: str
    short_code: str
    short_url: str

@app.get("/d/{short_code}")
async def redirect_to_url(short_code: str, request: Request):
    result = load_urls()[short_code]
    if result:
        return RedirectResponse(url=result)
    else:
        raise HTTPException(status_code=404, detail="Short URL not found")

@app.post("/api/shorten", response_model=URLResponse)
async def create_short_url(url_create: URLCreate, request: Request):
    if load_urls()[url_create.short_code]:
        raise HTTPException(status_code=409, detail="Short code already in use")    
    save_urls({url_create.short_code, url_create.url})
    
    # Construct base URL from request
    base_url = f"{request.url.scheme}://{request.url.netloc}"
    short_url = f"{base_url}/d/{url_create.short_code}"
    
    return URLResponse(
        url=url_create.url,
        short_code=url_create.short_code,
        short_url=short_url
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
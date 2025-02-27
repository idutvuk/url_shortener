from fastapi import FastAPI, HTTPException, Request
from fastapi.logger import logger
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import os
import json

app = FastAPI(title="URL Shortener")

SHORTENER_FILE = "shortened_urls.json"
@app.get("/api/urls")
def load_urls():
    if not os.path.exists(SHORTENER_FILE):
        logger.info(f"File {SHORTENER_FILE} does not exist. Returning empty dictionary.")
        return {}
    try:
        with open(SHORTENER_FILE, 'r') as f:
            urls = json.load(f)
            logger.info(f"Loaded URLs from {SHORTENER_FILE}")
            return urls
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from {SHORTENER_FILE}: {e}")
        return {}

def save_urls(urls):
    try:
        with open(SHORTENER_FILE, 'w') as f:
            json.dump(urls, f, indent=2)
            logger.info(f"Saved URLs to {SHORTENER_FILE}")
    except Exception as e:
        logger.error(f"Error saving URLs to {SHORTENER_FILE}: {e}")

class URLCreate(BaseModel):
    url: str
    short_code: str

class URLResponse(BaseModel):
    url: str
    short_code: str
    short_url: str

@app.get("/d/{short_code}")
async def redirect_to_url(short_code: str, request: Request):
    urls = load_urls()
    result = urls.get(short_code)
    if result:
        logger.info(f"Redirecting short code '{short_code}' to URL: {result}")
        return RedirectResponse(url=result)
    else:
        logger.warning(f"Short code '{short_code}' not found")
        raise HTTPException(status_code=404, detail="Short URL not found")

@app.post("/api/shorten", response_model=URLResponse)
async def create_short_url(url_create: URLCreate, request: Request):
    urls = load_urls()
    if url_create.short_code in urls:
        logger.warning(f"Short code '{url_create.short_code}' already in use")
        raise HTTPException(status_code=409, detail="Short code already in use")
    
    # Correcting the data structure to use a dictionary
    urls[url_create.short_code] = url_create.url
    save_urls(urls)
    
    # Construct base URL from request
    base_url = f"{request.url.scheme}://{request.url.netloc}"
    short_url = f"{base_url}/d/{url_create.short_code}"
    
    logger.info(f"Created short URL: {short_url} for original URL: {url_create.url}")
    return URLResponse(
        url=url_create.url,
        short_code=url_create.short_code,
        short_url=short_url
    )

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Uvicorn server on http://0.0.0.0:8003")
    uvicorn.run(app, host="0.0.0.0", port=8003, log_level=0 )

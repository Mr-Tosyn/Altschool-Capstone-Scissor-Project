from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import requests
from urllib.parse import urlparse

app = FastAPI()
templates = Jinja2Templates(directory="templates")

def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def shorten_url(url):
    if not is_valid_url(url):
        return None

    api_key = "your_api_key"
    api_url = f"https://api-ssl.bitly.com/v4/shorten"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "long_url": url
    }

    try:
        response = requests.post(api_url, json=payload, headers=headers)
        if response.status_code == 200:
            short_url = response.json()["link"]
            return short_url
        else:
            return None
    except Exception as e:
        return None

@app.post("/shorten/", response_class=HTMLResponse)
async def shorten(request: Request, long_url: str):
    shortened_url = shorten_url(long_url)
    return templates.TemplateResponse("index.html", {"request": request, "shortened_url": shortened_url})

@app.get("/", response_class=HTMLResponse)
async def read_item(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

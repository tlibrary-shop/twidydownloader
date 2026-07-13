import os
import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="TwidyDownloader API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/extract")
async def extract_info(url: str):
    rapidapi_key = os.environ.get("APIFY_TOKEN") # Tetap pakai nama variable ini di Render
    
    if not rapidapi_key:
        raise HTTPException(status_code=500, detail="API Token belum diatur di Render!")

    # API ini menggunakan endpoint GET dengan query parameter 'url'
    api_url = "https://social-media-video-downloader.p.rapidapi.com/smvd/get/all"
    querystring = {"url": url}
    headers = {
        "x-rapidapi-key": rapidapi_key,
        "x-rapidapi-host": "social-media-video-downloader.p.rapidapi.com"
    }

    try:
        response = requests.get(api_url, headers=headers, params=querystring, timeout=20)
        data = response.json()
        
        if "error" in data or not data.get("links"):
            raise Exception("API tidak menemukan video. Link mungkin private atau tidak valid.")

        formats = []
        for item in data.get("links", []):
            label = item.get("type", "Video").capitalize()
            kualitas = item.get("quality", "HD")
            formats.append({
                "label": f"{label} ({kualitas})",
                "ext": "mp4" if "video" in label.lower() else "mp3",
                "url": item.get("link")
            })

        return {
            "title": data.get("title", "Video Siap Diunduh"),
            "thumbnail": data.get("picture", ""),
            "formats": formats
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/{full_path:path}", response_class=HTMLResponse)
async def serve_spa(full_path: str):
    return FileResponse("static/index.html")

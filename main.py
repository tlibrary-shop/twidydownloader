import os
import requests
from fastapi import FastAPI, HTTPException, Request
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
    apify_token = os.environ.get("APIFY_TOKEN")
    if not apify_token:
        raise HTTPException(status_code=500, detail="APIFY_TOKEN belum diatur di Render!")

    # Router: Jika link adalah Instagram, gunakan Actor Instagram
    if "instagram.com" in url:
        actor_id = "apify/instagram-scraper" 
    else:
        # Placeholder jika suatu saat kamu tambah Actor lain
        raise HTTPException(status_code=400, detail="Saat ini hanya mendukung Instagram melalui API ini.")
        
    api_url = f"https://api.apify.com/v2/acts/{actor_id}/runs?token={apify_token}"
    
    payload = {"directUrls": [url]}
    
    try:
        run_response = requests.post(api_url, json=payload, timeout=15)
        run_data = run_response.json()
        run_id = run_data['data']['id']
        
        # Mengambil hasil
        result_url = f"https://api.apify.com/v2/acts/{actor_id}/runs/{run_id}/dataset/items?token={apify_token}"
        result_response = requests.get(result_url, timeout=20)
        items = result_response.json()
        
        if not items:
            raise Exception("Gagal mendapatkan data dari Instagram.")

        data = items[0]
        # Sesuaikan key 'videoUrl' atau 'displayUrl' sesuai struktur data Instagram
        video_url = data.get("videoUrl") or data.get("displayUrl")
        
        return {
            "title": data.get("captionText", "Download Instagram"),
            "thumbnail": data.get("displayUrl", ""),
            "formats": [{"label": "Video/Foto", "ext": "mp4", "url": video_url}]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/{full_path:path}", response_class=HTMLResponse)
async def serve_spa(full_path: str):
    return FileResponse("static/index.html")

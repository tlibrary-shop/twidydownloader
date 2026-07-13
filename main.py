import os
import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="TwidyDownloader API")

# Izinkan akses iFrame
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_iframe_headers(request: Request, call_next):
    response = await call_next(request)
    if "X-Frame-Options" in response.headers:
        del response.headers["X-Frame-Options"]
    response.headers["Content-Security-Policy"] = "frame-ancestors *"
    return response

@app.get("/api/extract")
async def extract_info(url: str):
    # Mengambil kunci rahasia dari Environment Variable Render
    rapidapi_key = os.environ.get("RAPIDAPI_KEY")
    
    if not rapidapi_key:
        raise HTTPException(status_code=500, detail="RAPIDAPI_KEY belum dipasang di pengaturan Environment Render!")

    # Target API yang kamu pilih (Auto Download All In One)
    api_url = "https://auto-download-all-in-one.p.rapidapi.com/v1/social/autolink"
    
    # API ini menggunakan format payload JSON dan metode POST
    payload = {"url": url}
    headers = {
        "x-rapidapi-key": rapidapi_key,
        "x-rapidapi-host": "auto-download-all-in-one.p.rapidapi.com",
        "Content-Type": "application/json"
    }

    try:
        # Mengirim URL ke API
        response = requests.post(api_url, json=payload, headers=headers, timeout=20)
        
        if response.status_code != 200:
            raise Exception("Gagal menghubungi API. Pastikan kamu sudah klik tombol biru 'Subscribe to Test' di RapidAPI dan kuota tersedia.")

        data = response.json()
        
        # Mengekstrak judul dan cover
        title = data.get("title", "File Siap Diunduh!")
        thumbnail = data.get("cover", "") 
        
        formats = []
        medias = data.get("medias", [])
        
        if not medias:
            raise Exception("API tidak menemukan link download untuk video ini. Link mungkin di-private.")

        # Memisahkan hasil berdasarkan Video atau Audio
        for item in medias:
            link_url = item.get("url")
            if link_url:
                kualitas = item.get("quality", "HD")
                ext = item.get("extension", "mp4")
                tipe = item.get("type", "video")
                
                label = "Audio Only" if tipe == "audio" else f"Video ({kualitas})"
                formats.append({"label": label, "ext": ext, "url": link_url})

        return {
            "title": title,
            "thumbnail": thumbnail,
            "formats": formats
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Mount folder frontend
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/{full_path:path}", response_class=HTMLResponse)
async def serve_spa(full_path: str):
    return FileResponse("static/index.html")

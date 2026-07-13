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

    # Target API (Social Media Video Downloader)
    api_url = "https://social-media-video-downloader.p.rapidapi.com/smvd/get/all"
    querystring = {"url": url}
    
    headers = {
        "x-rapidapi-key": rapidapi_key,
        "x-rapidapi-host": "social-media-video-downloader.p.rapidapi.com"
    }

    try:
        # Mengirim URL sosial media ke RapidAPI
        response = requests.get(api_url, headers=headers, params=querystring, timeout=15)
        
        # Jika API menolak akses (misal: kunci salah atau kuota habis)
        if response.status_code != 200:
            raise Exception("Gagal menghubungi server pengunduh. Pastikan kuota gratis RapidAPI masih tersedia.")

        data = response.json()
        
        # Deteksi pesan error langsung dari balasan API
        if "error" in data or data.get("message") == "You are not subscribed to this API.":
            raise Exception(data.get("message", "API gagal memproses link ini. Mungkin link diprivate atau salah."))

        # Mengekstrak judul dan gambar thumbnail
        title = data.get("title", "File Siap Diunduh!")
        thumbnail = data.get("picture", "")
        links = data.get("links", [])
        
        if not links:
            raise Exception("Tidak ada link download video/audio yang ditemukan untuk URL ini.")

        result_links = []
        
        # Membaca daftar format (Video MP4 / Audio MP3) dari API
        for item in links:
            tipe = item.get("type", "video") # Biasanya API membalas dengan 'video' atau 'audio'
            kualitas = item.get("quality", "HD")
            link_url = item.get("link", "")
            
            if link_url:
                if tipe == "audio":
                    result_links.append({"label": "Audio Only", "ext": "mp3", "url": link_url})
                else:
                    result_links.append({"label": f"Video ({kualitas})", "ext": "mp4", "url": link_url})

        return {
            "title": title,
            "thumbnail": thumbnail,
            "formats": result_links
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Mount folder frontend
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/{full_path:path}", response_class=HTMLResponse)
async def serve_spa(full_path: str):
    return FileResponse("static/index.html")

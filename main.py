from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp

app = FastAPI(title="TwidyDownloader API")

# 1. Middleware: Izinkan akses iFrame dan CORS
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
    # Hapus header pembatasan iFrame bawaan server jika ada
    response.headers.pop("X-Frame-Options", None)
    # Izinkan embed di semua domain
    response.headers["Content-Security-Policy"] = "frame-ancestors *"
    return response

# 2. Endpoint API yt-dlp
@app.get("/api/extract")
async def extract_info(url: str):
    ydl_opts = {
        'quiet': True, 
        'skip_download': True,
        'no_warnings': True
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Saring format agar response API tidak terlalu berat
            filtered_formats = []
            for f in info.get("formats", []):
                if f.get("url") and f.get("vcodec") != "none" or f.get("acodec") != "none":
                    filtered_formats.append({
                        "ext": f.get("ext", ""),
                        "resolution": f.get("resolution", "Audio Only"),
                        "url": f.get("url")
                    })
                    
            return {
                "title": info.get("title", "Unknown Title"),
                "thumbnail": info.get("thumbnail", ""),
                "formats": filtered_formats
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# 3. Mount folder static untuk CSS & JS
app.mount("/static", StaticFiles(directory="static"), name="static")

# 4. Catch-all Route untuk SPA Frontend (SEO Friendly tanpa #)
# Route ini diletakkan paling bawah agar tidak menabrak endpoint /api
@app.get("/{full_path:path}", response_class=HTMLResponse)
async def serve_spa(full_path: str):
    return FileResponse("static/index.html")

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp

app = FastAPI(title="TwidyDownloader API")

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
    ydl_opts = {
        'quiet': True, 
        'skip_download': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'geo_bypass': True,
        'extractor_args': {
            'youtube': {'player_client': ['android', 'web']}
        },
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            formats = info.get("formats", [])
            result_links = []
            
            video_audio = [f for f in formats if f.get("vcodec") != "none" and f.get("acodec") != "none"]
            if video_audio:
                best_va = video_audio[-1]
                result_links.append({
                    "label": f"Video ({best_va.get('resolution', 'HD')})", 
                    "ext": best_va.get("ext", "mp4"), 
                    "url": best_va.get("url")
                })
            elif info.get("url"):
                result_links.append({
                    "label": "Video (Utuh)", 
                    "ext": info.get("ext", "mp4"), 
                    "url": info.get("url")
                })
                
            audio_only = [f for f in formats if f.get("acodec") != "none" and f.get("vcodec") == "none"]
            if audio_only:
                best_a = audio_only[-1]
                result_links.append({
                    "label": "Audio Only", 
                    "ext": best_a.get("ext", "mp3"), 
                    "url": best_a.get("url")
                })

            unique_links = {v['label']: v for v in result_links}.values()

            return {
                "title": info.get("title", "Judul Tidak Diketahui"),
                "thumbnail": info.get("thumbnail", ""),
                "formats": list(unique_links)
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/{full_path:path}", response_class=HTMLResponse)
async def serve_spa(full_path: str):
    return FileResponse("static/index.html")

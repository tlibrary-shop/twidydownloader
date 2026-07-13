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
        # Trik 1: Menyamar sebagai aplikasi HP Android/iOS untuk menembus blokir YouTube & IG
        'extractor_args': {
            'youtube': {'player_client': ['android', 'ios']}
        },
        # Trik 2: Memalsukan identitas Browser (User-Agent) menjadi iPhone
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        },
        # Trik 3: Memaksa mesin mencari MP4 dengan resolusi maksimal 720p (karena di atas 720p YouTube memisahkan suara dan video)
        'format_sort': ['res:720', 'ext:mp4:m4a']
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            formats = info.get("formats", [])
            result_links = []
            
            # Hindari format streaming patah-patah (m3u8/dash) karena tidak bisa diklik download langsung oleh pengunjung
            valid_formats = [f for f in formats if f.get('protocol', '').startswith(('http', 'https'))]
            
            # --- 1. CARI VIDEO + AUDIO (Pre-merged MP4) ---
            video_formats = [f for f in valid_formats if f.get('vcodec') != 'none' and f.get('acodec') != 'none']
            
            if video_formats:
                # Ambil kualitas yang berbeda (Maksimal 2 pilihan agar user tidak bingung)
                seen_res = set()
                for f in reversed(video_formats):
                    res = f.get('resolution', 'HD')
                    ext = f.get('ext', 'mp4')
                    # Keamanan ganda: pastikan sistem tidak salah memasukkan mp3 ke dalam kolom video
                    if res not in seen_res and res != 'audio only' and ext != 'mp3':
                        result_links.append({
                            "label": f"Video ({res})",
                            "ext": ext,
                            "url": f.get('url')
                        })
                        seen_res.add(res)
                        if len(seen_res) >= 2: 
                            break
                            
            # --- 2. FALLBACK UNTUK TIKTOK, TWITTER, & IG ---
            # Platform ini sering menyembunyikan videonya di luar list 'formats'
            if not result_links and info.get('url'):
                ext = info.get('ext', 'mp4')
                # Keamanan ganda lagi
                if ext != 'mp3' and ext != 'm4a':
                    result_links.append({
                        "label": "Video (Utuh)",
                        "ext": ext,
                        "url": info.get('url')
                    })

            # --- 3. CARI AUDIO ONLY (MP3/M4A) ---
            audio_formats = [f for f in valid_formats if f.get('acodec') != 'none' and f.get('vcodec') == 'none']
            if audio_formats:
                best_audio = audio_formats[-1]
                result_links.append({
                    "label": "Audio Only",
                    "ext": best_audio.get('ext', 'mp3'),
                    "url": best_audio.get('url')
                })
            elif info.get('url') and info.get('ext') in ['mp3', 'm4a', 'wav']:
                # Jika aslinya memang link sound/musik
                result_links.append({
                    "label": "Audio Only",
                    "ext": info.get('ext', 'mp3'),
                    "url": info.get('url')
                })

            # Bersihkan dari link ganda/kembar
            final_links = []
            seen_urls = set()
            for link in result_links:
                if link['url'] not in seen_urls:
                    final_links.append(link)
                    seen_urls.add(link['url'])

            return {
                "title": info.get("title", "Video Siap Diunduh!"),
                "thumbnail": info.get("thumbnail", ""),
                "formats": final_links
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/{full_path:path}", response_class=HTMLResponse)
async def serve_spa(full_path: str):
    return FileResponse("static/index.html")

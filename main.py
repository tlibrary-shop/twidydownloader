from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp

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
    # Pengaturan dasar yang aman
    ydl_opts = {
        'quiet': True, 
        'skip_download': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'geo_bypass': True,
        # Maksimal cari resolusi 720p agar audio dan video tidak terpisah
        'format_sort': ['res:720', 'ext:mp4:m4a']
    }
    
    # ATURAN DINAMIS: Strategi berbeda untuk setiap sosmed agar tidak diblokir
    if "youtube.com" in url or "youtu.be" in url:
        # Trik YouTube: Menyamar sebagai aplikasi Android murni
        ydl_opts['extractor_args'] = {'youtube': {'player_client': ['android', 'web']}}
    elif "tiktok.com" in url:
        # Trik TikTok: JANGAN pakai User-Agent palsu, biarkan yt-dlp membaca API asli TikTok
        pass
    else:
        # Trik IG/Facebook/Twitter: Gunakan identitas browser komputer standar
        ydl_opts['http_headers'] = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            formats = info.get("formats", [])
            result_links = []
            
            # Buang format streaming m3u8 yang tidak bisa didownload langsung
            valid_formats = [f for f in formats if f.get('protocol', '').startswith(('http', 'https'))]
            
            # --- 1. AMBIL VIDEO ---
            video_formats = [f for f in valid_formats if f.get('vcodec') != 'none' and f.get('acodec') != 'none']
            if video_formats:
                seen_res = set()
                for f in reversed(video_formats):
                    res = f.get('resolution', 'HD')
                    ext = f.get('ext', 'mp4')
                    # Pastikan mp3 tidak masuk ke kategori video
                    if res not in seen_res and res != 'audio only' and ext != 'mp3':
                        result_links.append({"label": f"Video ({res})", "ext": ext, "url": f.get('url')})
                        seen_res.add(res)
                        if len(seen_res) >= 2: break
                            
            # Fallback jika platform menyembunyikan video (seperti TikTok)
            if not result_links and info.get('url'):
                ext = info.get('ext', 'mp4')
                if ext != 'mp3' and ext != 'm4a':
                    result_links.append({"label": "Video (Utuh)", "ext": ext, "url": info.get('url')})

            # --- 2. AMBIL AUDIO ---
            audio_formats = [f for f in valid_formats if f.get('acodec') != 'none' and f.get('vcodec') == 'none']
            if audio_formats:
                best_audio = audio_formats[-1]
                result_links.append({"label": "Audio Only", "ext": best_audio.get('ext', 'mp3'), "url": best_audio.get('url')})
            elif info.get('url') and info.get('ext') in ['mp3', 'm4a', 'wav']:
                result_links.append({"label": "Audio Only", "ext": info.get('ext', 'mp3'), "url": info.get('url')})

            # --- 3. BERSIHKAN LINK GANDA ---
            final_links = []
            seen_urls = set()
            for link in result_links:
                if link['url'] not in seen_urls:
                    final_links.append(link)
                    seen_urls.add(link['url'])

            return {
                "title": info.get("title", "File Siap Diunduh!"),
                "thumbnail": info.get("thumbnail", ""),
                "formats": final_links
            }
            
    except Exception as e:
        # Menerjemahkan log error yang rumit menjadi pesan yang mudah dipahami user
        error_msg = str(e)
        if "Sign in to confirm you're not a bot" in error_msg:
            raise HTTPException(status_code=400, detail="Server Render diblokir oleh keamanan Anti-Bot YouTube. Coba lagi nanti atau gunakan video lain.")
        elif "status code 8" in error_msg:
            raise HTTPException(status_code=400, detail="TikTok sedang membatasi akses server. Silakan coba beberapa saat lagi.")
        elif "Video unavailable" in error_msg:
            raise HTTPException(status_code=400, detail="Video ini di-private atau sudah dihapus.")
        else:
            raise HTTPException(status_code=400, detail="Gagal mengambil data. Pastikan link sudah benar atau platform sedang memblokir akses.")

# Mount folder frontend
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/{full_path:path}", response_class=HTMLResponse)
async def serve_spa(full_path: str):
    return FileResponse("static/index.html")

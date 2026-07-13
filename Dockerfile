# Gunakan image Python yang ringan
FROM python:3.11-slim

# Install FFmpeg untuk kebutuhan yt-dlp
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy dependency dan install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy semua file proyek
COPY . .

# Jalankan server Uvicorn untuk FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]



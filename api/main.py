"""UUMit Video Suite - Main Application"""
import os
from pathlib import Path
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from .utils.auth import verify_api_key
from .routers import (
    subtitle,
    transcript,
    silence,
    highlight,
    crop,
    watermark,
    compress,
    frames,
)

# Load env
load_dotenv()

# Ensure directories exist
os.makedirs(os.getenv("UPLOAD_DIR", "./uploads"), exist_ok=True)
os.makedirs(os.getenv("OUTPUT_DIR", "./outputs"), exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 UUMit Video Suite starting up...")
    yield
    logger.info("🛑 UUMit Video Suite shutting down...")


app = FastAPI(
    title="UUMit Video Suite",
    description="AI-powered Video Editing API Suite - Auto subtitle, transcript, silence removal, highlight extraction, crop, watermark, compression, frame extraction",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth middleware
app.middleware("http")(verify_api_key)

# Static file serving for downloads
output_dir = os.getenv("OUTPUT_DIR", "./outputs")
if Path(output_dir).exists():
    app.mount("/download", StaticFiles(directory=output_dir), name="download")


# ─── Health ───────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "uumit-video-suite",
        "version": "1.0.0",
        "endpoints": {
            "subtitle": "/v1/subtitle/generate",
            "subtitle_translate": "/v1/subtitle/translate",
            "transcript": "/v1/transcript",
            "silence_remove": "/v1/silence/remove",
            "highlight_extract": "/v1/highlight/extract",
            "crop_portrait": "/v1/crop/portrait",
            "watermark_add_text": "/v1/watermark/add-text",
            "watermark_add_image": "/v1/watermark/add-image",
            "watermark_remove": "/v1/watermark/remove",
            "compress": "/v1/compress",
            "frames_extract": "/v1/frames/extract",
        },
    }


# ─── API Docs ─────────────────────────────────────────────────────────
@app.get("/docs/pricing")
async def pricing():
    return {
        "pricing_model": "per_request",
        "unit": "UT",
        "rates": {
            "subtitle": {"price": 0.5, "unit": "per minute of video"},
            "subtitle_translate": {"price": 0.3, "unit": "per minute"},
            "transcript": {"price": 0.3, "unit": "per minute"},
            "silence_removal": {"price": 0.5, "unit": "per minute"},
            "highlight": {"price": 1.0, "unit": "per video"},
            "crop": {"price": 0.3, "unit": "per minute"},
            "watermark": {"price": 0.2, "unit": "per minute"},
            "compress": {"price": 0.3, "unit": "per minute"},
            "frames": {"price": 0.2, "unit": "per 100 frames"},
        },
        "free_tier": {"daily_limit": 3, "max_duration_seconds": 60},
    }


# ─── Register Routers ─────────────────────────────────────────────────
app.include_router(subtitle.router)
app.include_router(transcript.router)
app.include_router(silence.router)
app.include_router(highlight.router)
app.include_router(crop.router)
app.include_router(watermark.router)
app.include_router(compress.router)
app.include_router(frames.router)


# ─── Entry Point ──────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    uvicorn.run("api.main:app", host=host, port=port, reload=True)

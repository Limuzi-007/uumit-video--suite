"""File handling utilities"""
import os
import uuid
import shutil
from pathlib import Path
from fastapi import UploadFile, HTTPException

ALLOWED_VIDEO_EXTENSIONS = {
    ".mp4", ".mov", ".avi", ".mkv", ".webm", ".flv", ".wmv", ".m4v"
}
ALLOWED_AUDIO_EXTENSIONS = {
    ".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma"
}
ALLOWED_IMAGE_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".webp"
}

MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "524288000"))  # 500MB


def get_upload_dir() -> Path:
    path = Path(os.getenv("UPLOAD_DIR", "./uploads"))
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_output_dir() -> Path:
    path = Path(os.getenv("OUTPUT_DIR", "./outputs"))
    path.mkdir(parents=True, exist_ok=True)
    return path


def generate_filename(ext: str) -> str:
    return f"{uuid.uuid4().hex}{ext}"


def validate_video(file: UploadFile) -> str:
    """Validate video upload, return job_id."""
    ext = Path(file.filename or "video.mp4").suffix.lower()
    if ext not in ALLOWED_VIDEO_EXTENSIONS:
        raise HTTPException(400, f"Unsupported video format: {ext}")
    return ext


def validate_audio(file: UploadFile) -> str:
    ext = Path(file.filename or "audio.mp3").suffix.lower()
    if ext not in ALLOWED_AUDIO_EXTENSIONS:
        raise HTTPException(400, f"Unsupported audio format: {ext}")
    return ext


def validate_image(file: UploadFile) -> str:
    ext = Path(file.filename or "image.png").suffix.lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(400, f"Unsupported image format: {ext}")
    return ext


async def save_upload(file: UploadFile, subdir: str = "") -> Path:
    """Save uploaded file and return path."""
    ext = Path(file.filename or "file.bin").suffix.lower()
    base = get_upload_dir()
    if subdir:
        base = base / subdir
        base.mkdir(parents=True, exist_ok=True)

    filename = generate_filename(ext)
    dest = base / filename

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(413, f"File too large (max {MAX_FILE_SIZE // 1024 // 1024}MB)")

    with open(dest, "wb") as f:
        f.write(content)

    return dest


def cleanup(path: Path):
    """Remove file or directory."""
    try:
        if path.is_file() or path.is_symlink():
            path.unlink(missing_ok=True)
        elif path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
    except Exception:
        pass

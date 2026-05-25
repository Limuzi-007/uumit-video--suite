"""FFmpeg wrapper utilities"""
import os
import subprocess
import json
from pathlib import Path
from typing import Optional, List
from loguru import logger


def probe(path: Path) -> dict:
    """Get media file metadata using ffprobe."""
    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_format", "-show_streams",
        str(path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {result.stderr}")
    return json.loads(result.stdout)


def get_duration(path: Path) -> float:
    """Get media duration in seconds."""
    info = probe(path)
    return float(info.get("format", {}).get("duration", 0))


def get_resolution(path: Path) -> tuple[int, int]:
    """Get video resolution (width, height)."""
    info = probe(path)
    for stream in info.get("streams", []):
        if stream.get("codec_type") == "video":
            return (stream["width"], stream["height"])
    return (0, 0)


def extract_audio(input_path: Path, output_path: Path, sample_rate: int = 16000) -> Path:
    """Extract audio from video."""
    output_path = output_path.with_suffix(".wav")
    cmd = [
        "ffmpeg", "-y", "-i", str(input_path),
        "-vn", "-acodec", "pcm_s16le",
        "-ar", str(sample_rate), "-ac", "1",
        str(output_path)
    ]
    _run(cmd)
    return output_path


def run_ffmpeg(args: List[str], timeout: int = 600) -> subprocess.CompletedProcess:
    """Run ffmpeg with given args."""
    cmd = ["ffmpeg", "-y"] + args
    return _run(cmd, timeout)


def _run(cmd: List[str], timeout: int = 600) -> subprocess.CompletedProcess:
    logger.info(f"FFmpeg: {' '.join(cmd)}")
    result = subprocess.run(
        cmd, capture_output=True, text=True, timeout=timeout
    )
    if result.returncode != 0:
        logger.error(f"FFmpeg stderr: {result.stderr[:500]}")
        raise RuntimeError(f"FFmpeg failed: {result.stderr[:300]}")
    return result


def encode_subtitle(subtitle_path: Path, format: str = "srt") -> str:
    """Read subtitle file content."""
    with open(subtitle_path, "r", encoding="utf-8") as f:
        return f.read()

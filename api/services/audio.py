"""Audio processing services"""
import os
import whisper
from pathlib import Path
from typing import Optional
from loguru import logger

_MODEL = None


def _get_model(model_name: str = "base"):
    """Lazy-load whisper model."""
    global _MODEL
    if _MODEL is None:
        logger.info(f"Loading Whisper model: {model_name}")
        _MODEL = whisper.load_model(model_name)
    return _MODEL


def transcribe(audio_path: Path, language: str = "zh", word_timestamps: bool = False) -> dict:
    """Transcribe audio using Whisper."""
    model = _get_model()
    logger.info(f"Transcribing {audio_path} (lang={language})")

    result = model.transcribe(
        str(audio_path),
        language=language if language != "auto" else None,
        word_timestamps=word_timestamps,
        verbose=False
    )

    return {
        "text": result["text"].strip(),
        "segments": [
            {
                "id": seg["id"],
                "start": seg["start"],
                "end": seg["end"],
                "text": seg["text"].strip(),
                "words": seg.get("words", []),
            }
            for seg in result.get("segments", [])
        ],
        "language": result.get("language", language),
    }


def segments_to_srt(segments: list[dict]) -> str:
    """Convert whisper segments to SRT format."""
    lines = []
    for i, seg in enumerate(segments, 1):
        start = _fmt_time(seg["start"])
        end = _fmt_time(seg["end"])
        lines.append(f"{i}")
        lines.append(f"{start} --> {end}")
        lines.append(seg["text"])
        lines.append("")
    return "\n".join(lines)


def segments_to_vtt(segments: list[dict]) -> str:
    """Convert whisper segments to VTT format."""
    lines = ["WEBVTT", ""]
    for seg in segments:
        start = _fmt_time_vtt(seg["start"])
        end = _fmt_time_vtt(seg["end"])
        lines.append(f"{start} --> {end}")
        lines.append(seg["text"])
        lines.append("")
    return "\n".join(lines)


def _fmt_time(seconds: float) -> str:
    """Format seconds to SRT time: HH:MM:SS,mmm"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _fmt_time_vtt(seconds: float) -> str:
    """Format seconds to VTT time: HH:MM:SS.mmm"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"

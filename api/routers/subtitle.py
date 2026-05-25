"""Video Subtitle API - Auto subtitle generation & embedding"""
import os
import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from loguru import logger

from ..models import SubtitleRequest, SubtitleResponse, JobStatus
from ..services.ffmpeg_utils import extract_audio, get_duration, run_ffmpeg
from ..services.audio import transcribe, segments_to_srt, segments_to_vtt
from ..services.video import burn_subtitle
from ..utils.file import validate_video, save_upload, get_output_dir, generate_filename

router = APIRouter(prefix="/v1/subtitle", tags=["Subtitle"])


@router.post("/generate", response_model=SubtitleResponse)
async def generate_subtitle(
    file: UploadFile = File(...),
    language: str = Form("zh"),
    srt_format: str = Form("srt"),
    burn_in: bool = Form(False),
):
    """Generate subtitles from video/audio."""
    try:
        ext = validate_video(file)
        input_path = await save_upload(file, "subtitle_in")

        # Extract audio
        audio_path = input_path.with_suffix(".wav")
        audio_path = extract_audio(input_path, audio_path)

        # Transcribe
        result = transcribe(audio_path, language=language)

        # Generate subtitle file
        if srt_format == "srt":
            subtitle_content = segments_to_srt(result["segments"])
            sub_ext = ".srt"
        elif srt_format == "vtt":
            subtitle_content = segments_to_vtt(result["segments"])
            sub_ext = ".vtt"
        else:
            subtitle_content = segments_to_srt(result["segments"])
            sub_ext = ".srt"

        sub_filename = generate_filename(sub_ext)
        sub_path = get_output_dir() / sub_filename
        with open(sub_path, "w", encoding="utf-8") as f:
            f.write(subtitle_content)

        output_video_url = None
        if burn_in:
            output_path = burn_subtitle(input_path, sub_path)
            output_video_url = f"/download/{output_path.name}"
            # Also upload subtitle

        return SubtitleResponse(
            job_id=input_path.stem,
            status=JobStatus.completed,
            subtitle_url=f"/download/{sub_filename}",
            text=result["text"],
            segments=result["segments"],
        )
    except Exception as e:
        logger.error(f"Subtitle generation failed: {e}")
        raise HTTPException(500, detail=str(e))


@router.post("/translate", response_model=SubtitleResponse)
async def translate_subtitle(
    file: UploadFile = File(...),
    source_language: str = Form("zh"),
    target_language: str = Form("en"),
):
    """Translate subtitle file (SRT/VTT)."""
    try:
        input_path = await save_upload(file, "subtitle_translate")
        content = input_path.read_text(encoding="utf-8")

        from ..services.ai import translate_text

        # Parse and translate SRT
        new_lines = []
        for line in content.split("\n"):
            if line.strip() and not line.strip().isdigit() and "-->" not in line:
                new_lines.append(translate_text(line, source_language, target_language))
            else:
                new_lines.append(line)

        translated = "\n".join(new_lines)

        sub_filename = generate_filename(f"_{target_language}.srt")
        sub_path = get_output_dir() / sub_filename
        with open(sub_path, "w", encoding="utf-8") as f:
            f.write(translated)

        return SubtitleResponse(
            job_id=input_path.stem,
            status=JobStatus.completed,
            subtitle_url=f"/download/{sub_filename}",
            text=translated,
        )
    except Exception as e:
        logger.error(f"Subtitle translation failed: {e}")
        raise HTTPException(500, detail=str(e))

"""Video/Audio to Text API"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from loguru import logger

from ..models import TranscriptResponse, JobStatus
from ..services.ffmpeg_utils import extract_audio, get_duration
from ..services.audio import transcribe, segments_to_srt
from ..utils.file import validate_video, validate_audio, save_upload

router = APIRouter(prefix="/v1/transcript", tags=["Transcript"])


@router.post("", response_model=TranscriptResponse)
async def video_to_text(
    file: UploadFile = File(...),
    language: str = Form("zh"),
    word_timestamps: bool = Form(False),
):
    """Convert video/audio to text transcript."""
    try:
        # Accept both video and audio
        audio_path = None
        ext = None

        try:
            ext = validate_video(file)
        except HTTPException:
            ext = validate_audio(file)

        input_path = await save_upload(file, "transcript_in")

        if ext in (".mp4", ".mov", ".avi", ".mkv", ".webm", ".flv", ".wmv", ".m4v"):
            audio_path = input_path.with_suffix(".wav")
            audio_path = extract_audio(input_path, audio_path)
        else:
            audio_path = input_path

        # Transcribe
        result = transcribe(audio_path, language=language, word_timestamps=word_timestamps)
        duration = get_duration(audio_path)

        return TranscriptResponse(
            job_id=input_path.stem,
            status=JobStatus.completed,
            text=result["text"],
            segments=result["segments"],
            duration_seconds=duration,
        )
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        raise HTTPException(500, detail=str(e))

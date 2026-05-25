"""Silence Removal API"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from loguru import logger

from ..models import SilenceRemovalResponse, JobStatus
from ..services.video import remove_silence
from ..utils.file import validate_video, save_upload

router = APIRouter(prefix="/v1/silence", tags=["Silence Removal"])


@router.post("/remove", response_model=SilenceRemovalResponse)
async def remove_silence_endpoint(
    file: UploadFile = File(...),
    silence_threshold: float = Form(-30),
    min_silence_duration: float = Form(0.5),
    padding: float = Form(0.1),
):
    """Remove silent segments from video."""
    try:
        validate_video(file)
        input_path = await save_upload(file, "silence_in")

        output_path, original_dur, trimmed_dur, removed = remove_silence(
            input_path,
            silence_threshold=silence_threshold,
            min_silence_duration=min_silence_duration,
            padding=padding,
        )

        return SilenceRemovalResponse(
            job_id=input_path.stem,
            status=JobStatus.completed,
            output_url=f"/download/{output_path.name}",
            original_duration=original_dur,
            trimmed_duration=trimmed_dur,
            segments_removed=removed,
        )
    except Exception as e:
        logger.error(f"Silence removal failed: {e}")
        raise HTTPException(500, detail=str(e))

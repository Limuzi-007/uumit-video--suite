"""Highlight Extraction API"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from loguru import logger

from ..models import HighlightResponse, JobStatus
from ..services.video import detect_highlights_motion, concat_clips
from ..utils.file import validate_video, save_upload

router = APIRouter(prefix="/v1/highlight", tags=["Highlight Extraction"])


@router.post("/extract", response_model=HighlightResponse)
async def extract_highlights(
    file: UploadFile = File(...),
    method: str = Form("motion"),
    target_duration: int = Form(60),
    num_clips: int = Form(5),
):
    """Extract highlight clips from video."""
    try:
        validate_video(file)
        input_path = await save_upload(file, "highlight_in")

        clips = detect_highlights_motion(
            input_path,
            target_duration=target_duration,
            num_clips=num_clips,
        )

        if not clips:
            raise HTTPException(400, "No highlight scenes detected")

        output_path = concat_clips(input_path, clips)

        return HighlightResponse(
            job_id=input_path.stem,
            status=JobStatus.completed,
            clips=clips,
            output_url=f"/download/{output_path.name}",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Highlight extraction failed: {e}")
        raise HTTPException(500, detail=str(e))

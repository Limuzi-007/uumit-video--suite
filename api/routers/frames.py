"""Frame Extraction API"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from loguru import logger

from ..models import FrameExtractionResponse, JobStatus
from ..services.video import extract_frames
from ..utils.file import validate_video, save_upload, get_output_dir
from pathlib import Path

router = APIRouter(prefix="/v1/frames", tags=["Frame Extraction"])


@router.post("/extract", response_model=FrameExtractionResponse)
async def extract_video_frames(
    file: UploadFile = File(...),
    fps: float = Form(None),
    interval: float = Form(None),
    format: str = Form("jpg"),
    max_frames: int = Form(100),
):
    """Extract frames from video."""
    try:
        validate_video(file)
        input_path = await save_upload(file, "frames_in")

        frames, zip_path = extract_frames(
            input_path,
            fps=fps,
            interval=interval,
            img_format=format,
            max_frames=max_frames,
        )

        frame_urls = [f"/frames/{f.name}" for f in frames]

        return FrameExtractionResponse(
            job_id=input_path.stem,
            status=JobStatus.completed,
            frames=frame_urls,
            total_frames=len(frames),
            zip_url=f"/download/{zip_path.name}",
        )
    except Exception as e:
        logger.error(f"Frame extraction failed: {e}")
        raise HTTPException(500, detail=str(e))

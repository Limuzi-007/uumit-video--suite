"""Horizontal to Vertical Crop API"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from loguru import logger

from ..models import CropResponse, JobStatus
from ..services.video import crop_to_portrait
from ..utils.file import validate_video, save_upload

router = APIRouter(prefix="/v1/crop", tags=["Crop & Resize"])


@router.post("/portrait", response_model=CropResponse)
async def crop_portrait(
    file: UploadFile = File(...),
    aspect_ratio: str = Form("9:16"),
    strategy: str = Form("center"),
):
    """Crop horizontal video to portrait/short-form format."""
    try:
        validate_video(file)
        input_path = await save_upload(file, "crop_in")

        output_path = crop_to_portrait(
            input_path,
            aspect_ratio=aspect_ratio,
            strategy=strategy,
        )

        return CropResponse(
            job_id=input_path.stem,
            status=JobStatus.completed,
            output_url=f"/download/{output_path.name}",
        )
    except Exception as e:
        logger.error(f"Crop failed: {e}")
        raise HTTPException(500, detail=str(e))

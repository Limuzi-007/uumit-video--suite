"""Watermark Add/Remove API"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pathlib import Path
from loguru import logger

from ..models import WatermarkResponse, JobStatus
from ..services.video import add_watermark_text, add_watermark_image, remove_watermark_ai
from ..utils.file import validate_video, validate_image, save_upload

router = APIRouter(prefix="/v1/watermark", tags=["Watermark"])


@router.post("/add-text", response_model=WatermarkResponse)
async def add_text_watermark(
    file: UploadFile = File(...),
    text: str = Form(...),
    position: str = Form("br"),
    opacity: float = Form(0.7),
    scale: float = Form(0.15),
):
    """Add text watermark to video."""
    try:
        validate_video(file)
        input_path = await save_upload(file, "wm_in")

        output_path = add_watermark_text(
            input_path,
            text=text,
            position=position,
            opacity=opacity,
            scale=scale,
        )

        return WatermarkResponse(
            job_id=input_path.stem,
            status=JobStatus.completed,
            output_url=f"/download/{output_path.name}",
        )
    except Exception as e:
        logger.error(f"Add text watermark failed: {e}")
        raise HTTPException(500, detail=str(e))


@router.post("/add-image", response_model=WatermarkResponse)
async def add_image_watermark(
    video: UploadFile = File(...),
    logo: UploadFile = File(...),
    position: str = Form("br"),
    opacity: float = Form(0.7),
    scale: float = Form(0.15),
):
    """Add image watermark to video."""
    try:
        validate_video(video)
        validate_image(logo)

        video_path = await save_upload(video, "wm_in")
        logo_path = await save_upload(logo, "wm_logos")

        output_path = add_watermark_image(
            video_path,
            logo_path,
            position=position,
            opacity=opacity,
            scale=scale,
        )

        return WatermarkResponse(
            job_id=video_path.stem,
            status=JobStatus.completed,
            output_url=f"/download/{output_path.name}",
        )
    except Exception as e:
        logger.error(f"Add image watermark failed: {e}")
        raise HTTPException(500, detail=str(e))


@router.post("/remove", response_model=WatermarkResponse)
async def remove_watermark(
    file: UploadFile = File(...),
):
    """Remove watermark from video (basic AI detection)."""
    try:
        validate_video(file)
        input_path = await save_upload(file, "wm_remove_in")

        output_path = remove_watermark_ai(input_path)

        return WatermarkResponse(
            job_id=input_path.stem,
            status=JobStatus.completed,
            output_url=f"/download/{output_path.name}",
        )
    except Exception as e:
        logger.error(f"Remove watermark failed: {e}")
        raise HTTPException(500, detail=str(e))

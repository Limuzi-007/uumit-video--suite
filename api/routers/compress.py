"""Video Compression API"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from loguru import logger

from ..models import CompressionResponse, JobStatus
from ..services.video import compress_video
from ..utils.file import validate_video, save_upload

router = APIRouter(prefix="/v1/compress", tags=["Compression"])


@router.post("", response_model=CompressionResponse)
async def compress(
    file: UploadFile = File(...),
    crf: int = Form(28),
    codec: str = Form("h264"),
    resolution: str = Form(None),
    bitrate: str = Form(None),
):
    """Compress video with configurable quality."""
    try:
        validate_video(file)
        input_path = await save_upload(file, "compress_in")

        output_path, original_size, compressed_size, ratio = compress_video(
            input_path,
            crf=crf,
            codec=codec,
            resolution=resolution,
            bitrate=bitrate,
        )

        return CompressionResponse(
            job_id=input_path.stem,
            status=JobStatus.completed,
            output_url=f"/download/{output_path.name}",
            original_size=original_size,
            compressed_size=compressed_size,
            compression_ratio=round(ratio, 2),
        )
    except Exception as e:
        logger.error(f"Compression failed: {e}")
        raise HTTPException(500, detail=str(e))

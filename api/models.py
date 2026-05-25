"""Request/Response models for all endpoints"""
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


# ─── Job Status ───────────────────────────────────────────────────────
class JobStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


# ─── Subtitle ─────────────────────────────────────────────────────────
class SubtitleFormat(str, Enum):
    srt = "srt"
    vtt = "vtt"
    ass = "ass"
    embedded = "embedded"  # burn into video


class SubtitleRequest(BaseModel):
    language: str = Field("zh", description="Source language code (zh/en/ja/ko)")
    format: SubtitleFormat = Field(SubtitleFormat.srt)
    burn_in: bool = Field(False, description="Burn subtitles into video")


class SubtitleResponse(BaseModel):
    job_id: str
    status: JobStatus
    subtitle_url: Optional[str] = None
    text: Optional[str] = None
    segments: Optional[List[dict]] = None


# ─── Transcript ────────────────────────────────────────────────────────
class TranscriptRequest(BaseModel):
    language: str = Field("zh")
    word_timestamps: bool = Field(False)
    speaker_diarization: bool = Field(False)


class TranscriptResponse(BaseModel):
    job_id: str
    status: JobStatus
    text: str = ""
    segments: List[dict] = []
    duration_seconds: float = 0


# ─── Silence Removal ───────────────────────────────────────────────────
class SilenceRemovalRequest(BaseModel):
    silence_threshold: float = Field(-30, description="dB threshold for silence")
    min_silence_duration: float = Field(0.5, description="Min silence duration in seconds")
    padding: float = Field(0.1, description="Padding to keep around speech")


class SilenceRemovalResponse(BaseModel):
    job_id: str
    status: JobStatus
    output_url: Optional[str] = None
    original_duration: float = 0
    trimmed_duration: float = 0
    segments_removed: int = 0


# ─── Highlight Extraction ─────────────────────────────────────────────
class HighlightRequest(BaseModel):
    method: str = Field("motion", description="highlight/motion/audio_energy")
    target_duration: int = Field(60, description="Target output duration in seconds")
    num_clips: int = Field(5, description="Number of highlight clips")


class HighlightResponse(BaseModel):
    job_id: str
    status: JobStatus
    clips: List[dict] = []
    output_url: Optional[str] = None


# ─── Horizontal to Vertical (Crop) ────────────────────────────────────
class AspectRatio(str, Enum):
    portrait_9_16 = "9:16"
    portrait_4_5 = "4:5"
    square_1_1 = "1:1"


class CropStrategy(str, Enum):
    center = "center"
    face_tracking = "face_tracking"
    motion_tracking = "motion_tracking"


class CropRequest(BaseModel):
    aspect_ratio: AspectRatio = Field(AspectRatio.portrait_9_16)
    strategy: CropStrategy = Field(CropStrategy.center)


class CropResponse(BaseModel):
    job_id: str
    status: JobStatus
    output_url: Optional[str] = None


# ─── Watermark ─────────────────────────────────────────────────────────
class WatermarkPosition(str, Enum):
    top_left = "tl"
    top_right = "tr"
    bottom_left = "bl"
    bottom_right = "br"
    center = "center"


class WatermarkAction(str, Enum):
    add = "add"
    remove = "remove"


class WatermarkRequest(BaseModel):
    action: WatermarkAction
    watermark_text: Optional[str] = None
    watermark_image_url: Optional[str] = None
    position: WatermarkPosition = WatermarkPosition.bottom_right
    opacity: float = Field(0.7, ge=0, le=1)
    scale: float = Field(0.15, description="Watermark size relative to video width")


class WatermarkResponse(BaseModel):
    job_id: str
    status: JobStatus
    output_url: Optional[str] = None


# ─── Translation ──────────────────────────────────────────────────────
class TranslateRequest(BaseModel):
    source_language: str = Field("zh")
    target_language: str = Field("en")


class TranslateResponse(BaseModel):
    job_id: str
    status: JobStatus
    translated_srt: Optional[str] = None
    output_url: Optional[str] = None


# ─── Compression ───────────────────────────────────────────────────────
class VideoCodec(str, Enum):
    h264 = "h264"
    h265 = "h265"
    vp9 = "vp9"


class CompressionRequest(BaseModel):
    crf: int = Field(28, ge=18, le=51, description="Quality (lower = better)")
    codec: VideoCodec = Field(VideoCodec.h264)
    resolution: Optional[str] = Field(None, description="e.g. 1280x720")
    bitrate: Optional[str] = Field(None, description="e.g. 2M")


class CompressionResponse(BaseModel):
    job_id: str
    status: JobStatus
    output_url: Optional[str] = None
    original_size: int = 0
    compressed_size: int = 0
    compression_ratio: float = 0


# ─── Frame Extraction ──────────────────────────────────────────────────
class FrameFormat(str, Enum):
    jpg = "jpg"
    png = "png"


class FrameExtractionRequest(BaseModel):
    fps: Optional[float] = Field(None, description="Frames per second")
    interval: Optional[float] = Field(None, description="Extract every N seconds")
    format: FrameFormat = FrameFormat.jpg
    max_frames: int = Field(100, description="Maximum frames to extract")


class FrameExtractionResponse(BaseModel):
    job_id: str
    status: JobStatus
    frames: List[str] = []
    total_frames: int = 0
    zip_url: Optional[str] = None


# ─── Generic Job Status ───────────────────────────────────────────────
class JobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    progress: float = 0
    result: Optional[dict] = None
    error: Optional[str] = None

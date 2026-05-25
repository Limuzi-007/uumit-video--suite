"""Video processing services"""
import os
import json
import subprocess
import math
import shutil
from pathlib import Path
from typing import Optional
from loguru import logger

from .ffmpeg_utils import run_ffmpeg, probe, get_duration, get_resolution
from ..utils.file import get_output_dir, generate_filename


def burn_subtitle(
    video_path: Path,
    srt_path: Path,
    output_path: Optional[Path] = None,
) -> Path:
    """Burn subtitles into video."""
    if output_path is None:
        output_path = get_output_dir() / generate_filename(".mp4")

    run_ffmpeg([
        "-i", str(video_path),
        "-vf", f"subtitles={str(srt_path)}",
        "-c:a", "aac",
        "-preset", "medium",
        str(output_path)
    ])
    return output_path


def remove_silence(
    video_path: Path,
    silence_threshold: float = -30,
    min_silence_duration: float = 0.5,
    padding: float = 0.1,
) -> tuple[Path, float, float, int]:
    """
    Remove silent segments from video.
    Returns (output_path, original_duration, trimmed_duration, segments_removed).
    """
    output_path = get_output_dir() / generate_filename(".mp4")
    original_dur = get_duration(video_path)

    # Step 1: Detect silence
    detect_cmd = [
        "ffmpeg", "-y", "-i", str(video_path),
        "-af", f"silencedetect=noise={silence_threshold}dB:d={min_silence_duration}",
        "-f", "null", "-"
    ]
    result = subprocess.run(detect_cmd, capture_output=True, text=True, timeout=300)
    stderr = result.stderr

    # Parse silence detection output
    silences = []
    for line in stderr.split("\n"):
        if "silence_start:" in line:
            start = float(line.split("silence_start:")[1].strip().split()[0])
            silences.append({"start": start})
        elif "silence_end:" in line:
            if silences:
                parts = line.split("silence_end:")
                end = float(parts[1].strip().split("|")[0].strip())
                silences[-1]["end"] = end

    if not silences:
        logger.info("No silence detected, copying original")
        shutil.copy2(video_path, output_path)
        return output_path, original_dur, original_dur, 0

    # Build filter to remove silence
    # Use aselect filter to keep non-silent segments
    segments_to_keep = []
    last_end = 0.0

    for s in silences:
        seg_start = last_end
        seg_end = max(0, s["start"] - padding)
        if seg_end > seg_start:
            segments_to_keep.append((seg_start, seg_end))
        last_end = max(last_end, s.get("end", s["start"]) + padding)

    # Trailing segment
    if last_end < original_dur:
        segments_to_keep.append((last_end, original_dur))

    if not segments_to_keep:
        raise RuntimeError("No audio segments remain after silence removal")

    # Build concat filter
    filter_parts = []
    for i, (start, end) in enumerate(segments_to_keep):
        dur = end - start
        filter_parts.append(
            f"[0:v]trim=start={start}:duration={dur},setpts=PTS-STARTPTS[v{i}];"
            f"[0:a]atrim=start={start}:duration={dur},asetpts=PTS-STARTPTS[a{i}]"
        )

    streams_v = "".join(f"[v{i}]" for i in range(len(segments_to_keep)))
    streams_a = "".join(f"[a{i}]" for i in range(len(segments_to_keep)))
    filter_parts.append(f"{streams_v}concat=n={len(segments_to_keep)}:v=1:a=0[outv]")
    filter_parts.append(f"{streams_a}concat=n={len(segments_to_keep)}:v=0:a=1[outa]")

    filter_str = ";".join(filter_parts)
    trimmed_dur = sum(end - start for start, end in segments_to_keep)

    run_ffmpeg([
        "-i", str(video_path),
        "-filter_complex", filter_str,
        "-map", "[outv]", "-map", "[outa]",
        "-c:v", "libx264", "-preset", "fast",
        "-c:a", "aac",
        str(output_path)
    ])

    return output_path, original_dur, trimmed_dur, len(silences)


def detect_highlights_motion(video_path: Path, target_duration: int = 60, num_clips: int = 5) -> list[dict]:
    """
    Detect high-motion segments (potentially highlights).
    Returns sorted list of clip segments.
    """
    # Use scene detection via ffmpeg
    detect_cmd = [
        "ffmpeg", "-y", "-i", str(video_path),
        "-filter:v", "select='gt(scene,0.3)',showinfo",
        "-f", "null", "-"
    ]
    result = subprocess.run(detect_cmd, capture_output=True, text=True, timeout=300)

    # Parse scene change timestamps
    scene_changes = []
    for line in result.stderr.split("\n"):
        if "pts_time:" in line:
            try:
                pts = float(line.split("pts_time:")[1].strip().split()[0])
                scene_changes.append(pts)
            except (ValueError, IndexError):
                pass

    if not scene_changes:
        # Fallback: evenly split
        dur = get_duration(video_path)
        segment_dur = min(dur / num_clips, target_duration / num_clips)
        scene_changes = [i * segment_dur for i in range(1, num_clips)]

    # Group nearby scene changes
    min_gap = 2.0
    grouped = []
    for t in sorted(scene_changes):
        if not grouped or t - grouped[-1] > min_gap:
            grouped.append(t)

    # Create clips around key changes
    dur = get_duration(video_path)
    clip_duration = min(target_duration / num_clips, 30)
    clips = []

    for i, change_time in enumerate(grouped[:num_clips]):
        start = max(0, change_time - 2)
        end = min(dur, start + clip_duration)
        if end - start > 1:
            clips.append({
                "start": round(start, 2),
                "end": round(end, 2),
                "duration": round(end - start, 2),
            })

    return clips


def concat_clips(
    video_path: Path,
    clips: list[dict],
    output_path: Optional[Path] = None,
) -> Path:
    """Concatenate highlight clips into one video."""
    if output_path is None:
        output_path = get_output_dir() / generate_filename("_highlight.mp4")

    # Create concat file
    concat_dir = get_output_dir() / "concat_tmp"
    concat_dir.mkdir(parents=True, exist_ok=True)

    concat_file = concat_dir / "segments.txt"
    with open(concat_file, "w") as f:
        for clip in clips:
            f.write(f"file '{video_path.absolute()}'\n")
            f.write(f"inpoint {clip['start']}\n")
            f.write(f"outpoint {clip['end']}\n")

    run_ffmpeg([
        "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        "-c", "copy",
        str(output_path)
    ])

    # Cleanup
    shutil.rmtree(concat_dir, ignore_errors=True)
    return output_path


def crop_to_portrait(
    video_path: Path,
    aspect_ratio: str = "9:16",
    strategy: str = "center",
    output_path: Optional[Path] = None,
) -> Path:
    """Crop horizontal video to portrait/short-form aspect ratio."""
    if output_path is None:
        output_path = get_output_dir() / generate_filename("_portrait.mp4")

    width, height = get_resolution(video_path)

    # Parse target ratio
    if aspect_ratio == "9:16":
        target_w = int(height * 9 / 16)
        target_h = height
    elif aspect_ratio == "4:5":
        target_w = int(height * 4 / 5)
        target_h = height
    elif aspect_ratio == "1:1":
        target_w = min(width, height)
        target_h = target_w
    else:
        target_w = int(height * 9 / 16)
        target_h = height

    if target_w > width:
        # Video is already taller than target, scale instead
        target_h = int(width * 16 / 9)
        target_w = width

    if strategy == "center":
        crop_filter = f"crop={target_w}:{target_h}:(iw-{target_w})/2:(ih-{target_h})/2"
    elif strategy == "face_tracking" or strategy == "motion_tracking":
        # For simplicity, use center + slight zoom for face/motion
        # Real face tracking needs OpenCV + dlib
        crop_filter = (
            f"crop={target_w}:{target_h}:(iw-{target_w})/2:(ih-{target_h})/2,"
            f"scale=iw*1.1:ih*1.1"
        )
    else:
        crop_filter = f"crop={target_w}:{target_h}:(iw-{target_w})/2:(ih-{target_h})/2"

    run_ffmpeg([
        "-i", str(video_path),
        "-vf", crop_filter,
        "-c:a", "aac",
        "-preset", "fast",
        str(output_path)
    ])
    return output_path


def add_watermark_text(
    video_path: Path,
    text: str,
    position: str = "br",
    opacity: float = 0.7,
    scale: float = 0.15,
    output_path: Optional[Path] = None,
) -> Path:
    """Add text watermark to video."""
    if output_path is None:
        output_path = get_output_dir() / generate_filename("_watermarked.mp4")

    # Position mapping
    pos_map = {
        "tl": "x=(w-text_w)/20:y=(h-text_h)/20",
        "tr": "x=w-text_w-(w/20):y=(h-text_h)/20",
        "bl": "x=(w-text_w)/20:y=h-text_h-(h/20)",
        "br": "x=w-text_w-(w/20):y=h-text_h-(h/20)",
        "center": "x=(w-text_w)/2:y=(h-text_h)/2",
    }
    pos = pos_map.get(position, pos_map["br"])
    alpha = f"{opacity:.2f}"

    # Font: use default sans-serif
    filter_str = (
        f"drawtext=text='{text}':"
        f"fontcolor=white@{alpha}:"
        f"fontsize={int(48 * scale * 10)}:"
        f"{pos}:"
        f"box=1:boxcolor=black@{max(0, opacity-0.5):.2f}:boxborderw=5"
    )

    run_ffmpeg([
        "-i", str(video_path),
        "-vf", filter_str,
        "-c:a", "copy",
        "-preset", "fast",
        str(output_path)
    ])
    return output_path


def remove_watermark_ai(
    video_path: Path,
    output_path: Optional[Path] = None,
) -> Path:
    """
    AI-based watermark removal.
    Note: This uses ffmpeg's delogo filter for known position.
    For production, use OpenCV inpainting or AI models.
    """
    if output_path is None:
        output_path = get_output_dir() / generate_filename("_clean.mp4")

    # Default: assume watermark in bottom-right quadrant
    width, height = get_resolution(video_path)
    x = int(width * 0.7)
    y = int(height * 0.85)
    w = int(width * 0.25)
    h = int(height * 0.1)

    run_ffmpeg([
        "-i", str(video_path),
        "-vf", f"delogo=x={x}:y={y}:w={w}:h={h}",
        "-c:a", "copy",
        str(output_path)
    ])
    return output_path


def add_watermark_image(
    video_path: Path,
    image_path: Path,
    position: str = "br",
    opacity: float = 0.7,
    scale: float = 0.15,
    output_path: Optional[Path] = None,
) -> Path:
    """Add image watermark (logo) to video."""
    if output_path is None:
        output_path = get_output_dir() / generate_filename("_watermarked.mp4")

    pos_map = {
        "tl": "(W-w)/20:(H-h)/20",
        "tr": "W-w-(W/20):(H-h)/20",
        "bl": "(W-w)/20:H-h-(H/20)",
        "br": "W-w-(W/20):H-h-(H/20)",
        "center": "(W-w)/2:(H-h)/2",
    }
    pos = pos_map.get(position, pos_map["br"])

    run_ffmpeg([
        "-i", str(video_path),
        "-i", str(image_path),
        "-filter_complex",
        f"[1:v]format=rgba,scale=iw*{scale}:ih*{scale}[logo];"
        f"[0:v][logo]overlay={pos}:format=auto,"
        f"colorchannelmixer=aa={opacity}[out]",
        "-map", "[out]", "-map", "0:a",
        "-c:a", "copy",
        "-preset", "fast",
        str(output_path)
    ])
    return output_path


def compress_video(
    video_path: Path,
    crf: int = 28,
    codec: str = "h264",
    resolution: Optional[str] = None,
    bitrate: Optional[str] = None,
    output_path: Optional[Path] = None,
) -> tuple[Path, int, int, float]:
    """Compress video with given parameters."""
    if output_path is None:
        output_path = get_output_dir() / generate_filename("_compressed.mp4")

    codec_map = {
        "h264": "libx264",
        "h265": "libx265",
        "vp9": "libvpx-vp9",
    }
    encoder = codec_map.get(codec, "libx264")
    ext_map = {"h264": ".mp4", "h265": ".mp4", "vp9": ".webm"}
    out_ext = ext_map.get(codec, ".mp4")
    if not str(output_path).endswith(out_ext):
        output_path = output_path.with_suffix(out_ext)

    original_size = video_path.stat().st_size

    args = ["-i", str(video_path)]
    if resolution:
        args += ["-vf", f"scale={resolution}"]
    args += ["-c:v", encoder, "-crf", str(crf)]
    if bitrate:
        args += ["-b:v", bitrate]
    if codec in ("h264", "h265"):
        args += ["-c:a", "aac", "-preset", "medium"]
    else:
        args += ["-c:a", "libopus"]

    args.append(str(output_path))
    run_ffmpeg(args)

    compressed_size = output_path.stat().st_size
    ratio = compressed_size / original_size if original_size > 0 else 1

    return output_path, original_size, compressed_size, ratio


def extract_frames(
    video_path: Path,
    fps: Optional[float] = None,
    interval: Optional[float] = None,
    img_format: str = "jpg",
    max_frames: int = 100,
) -> tuple[list[Path], Path]:
    """Extract frames from video."""
    output_dir = get_output_dir() / f"frames_{generate_filename('')}"
    output_dir.mkdir(parents=True, exist_ok=True)

    pattern = output_dir / f"frame_%05d.{img_format}"

    args = ["-i", str(video_path)]

    if fps:
        args += ["-vf", f"fps={fps}"]
    elif interval:
        args += ["-vf", f"fps=1/{interval}"]
    else:
        # Default: 1 frame per second
        args += ["-vf", "fps=1"]

    args += ["-frames:v", str(max_frames)]
    args.append(str(pattern))

    run_ffmpeg(args)

    # Collect frames
    frames = sorted(output_dir.glob(f"*.{img_format}"))

    # Zip them
    zip_path = get_output_dir() / f"frames_{generate_filename('')}.zip"
    shutil.make_archive(
        str(zip_path.with_suffix("")), "zip", output_dir
    )
    if not zip_path.exists():
        zip_path = Path(str(zip_path.with_suffix("")))
    # Fix zip path
    import zipfile
    with zipfile.ZipFile(get_output_dir() / f"frames_{generate_filename('')}.zip", 'w') as zf:
        for frame in frames:
            zf.write(frame, frame.name)

    # Get actual zip path
    return frames, zip_path

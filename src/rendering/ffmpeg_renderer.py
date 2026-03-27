import json
import os
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class RenderResult:
    out_path: str
    debug_path: str
    ffmpeg_cmd: list[str]


def _ensure_dir(path: str) -> None:
    Path(path).mkdir(parents=True, exist_ok=True)


def _q(s: str) -> str:
    """For debug logging only."""
    return shlex.quote(s)


def _get_job_title(job: Dict[str, Any]) -> str:
    publish = job.get("publish", {}) or {}
    title = (publish.get("title") or "").strip()
    return title or "STAY HARD"


def _get_background_local_path(job: Dict[str, Any]) -> str:
    assets = job.get("assets", {}) or {}
    bg_list = assets.get("background_clips", []) or []
    if not bg_list:
        raise ValueError("Job has no assets.background_clips[]")
    first = bg_list[0] or {}
    local_path = (first.get("local_path") or "").strip()
    if not local_path:
        raise ValueError("assets.background_clips[0].local_path is missing/empty")
    return local_path


def _get_music_spec(job: Dict[str, Any]) -> tuple[Optional[str], float]:
    """
    Returns (music_local_path, volume_db).
    volume_db defaults to -14.0 when music is provided but volume_db missing.
    If music_local_path missing, returns (None, 0.0).
    """
    assets = job.get("assets", {}) or {}
    music = assets.get("music") or {}
    if not isinstance(music, dict):
        return None, 0.0

    music_path = (music.get("local_path") or "").strip()
    if not music_path:
        return None, 0.0

    vol = music.get("volume_db", -14.0)
    try:
        vol = float(vol)
    except Exception:
        vol = -14.0

    return music_path, vol


def render_job_to_mp4(
    job: Dict[str, Any],
    job_id: str,
    duration_s: int = 55,
    width: int = 1080,
    height: int = 1920,
    fps: int = 30,
    out_dir: str = "tmp/renders",
) -> RenderResult:
    """
    Render a 1080x1920 MP4 (H.264 + AAC) from a local background clip,
    looping video to duration_s and drawing title text.

    Optional: If job.assets.music.local_path is present, it will be looped/trimmed
    to duration_s, volume-adjusted, and used as the ONLY audio (background audio muted).

    Output:
      tmp/renders/<job_id>.mp4
      tmp/renders/<job_id>.render_debug.json
    """
    _ensure_dir(out_dir)

    bg_path = _get_background_local_path(job)
    title = _get_job_title(job)
    music_path, music_volume_db = _get_music_spec(job)

    if not os.path.exists(bg_path):
        raise FileNotFoundError(f"Background clip not found: {bg_path}")

    if music_path and not os.path.exists(music_path):
        raise FileNotFoundError(f"Music file not found: {music_path}")

    out_path = str(Path(out_dir) / f"{job_id}.mp4")
    debug_path = str(Path(out_dir) / f"{job_id}.render_debug.json")

    # Video filter: scale/crop to 9:16, force fps, overlay title
    # Note: We avoid fontfile on Windows to reduce drawtext parsing issues.
    vf = (
        f"scale={width}:{height}:force_original_aspect_ratio=increase,"
        f"crop={width}:{height},fps={fps},"
        f"drawtext=text='{title}':"
        f"x=(w-text_w)/2:y=h*0.18:"
        f"fontsize=64:fontcolor=white:"
        f"box=1:boxcolor=black@0.35:boxborderw=24"
    )

    cmd: list[str] = [
        "ffmpeg",
        "-y",
        # Loop background video input
        "-stream_loop",
        "-1",
        "-i",
        bg_path,
    ]

    # If music provided, add as second input (also loop), then map audio from it only.
    if music_path:
        cmd += [
            "-stream_loop",
            "-1",
            "-i",
            music_path,
        ]

    # Filters
    cmd += ["-vf", vf]

    if music_path:
        # Mute background audio by mapping only the music input's audio.
        # Ensure exactly duration_s and apply volume.
        cmd += [
            "-filter:a",
            f"volume={music_volume_db}dB",
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
        ]
    else:
        # No music: keep background audio if present; if none, output will be silent.
        cmd += [
            "-map",
            "0:v:0",
            "-map",
            "0:a?",
        ]

    # Output encoding + timing
    cmd += [
        "-t",
        str(duration_s),
        "-r",
        str(fps),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-profile:v",
        "high",
        "-crf",
        "20",
        "-preset",
        "veryfast",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-ar",
        "48000",
        "-movflags",
        "+faststart",
        out_path,
    ]

    debug_payload = {
        "job_id": job_id,
        "duration_s": duration_s,
        "width": width,
        "height": height,
        "fps": fps,
        "background_path": bg_path,
        "music_path": music_path,
        "music_volume_db": music_volume_db if music_path else None,
        "out_path": out_path,
        "ffmpeg_cmd": cmd,
        "ffmpeg_cmd_pretty": " ".join(_q(x) for x in cmd),
    }
    _ensure_dir(str(Path(debug_path).parent))
    with open(debug_path, "w", encoding="utf-8") as f:
        json.dump(debug_payload, f, indent=2)

    # Run ffmpeg
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(
            "FFmpeg failed.\n"
            f"Command: {' '.join(_q(x) for x in cmd)}\n\n"
            f"STDOUT:\n{proc.stdout}\n\nSTDERR:\n{proc.stderr}\n"
        )

    return RenderResult(out_path=out_path, debug_path=debug_path, ffmpeg_cmd=cmd)
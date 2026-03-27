from __future__ import annotations

import json
import shlex
import subprocess
from pathlib import Path
from typing import Any


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _run(cmd: list[str]) -> None:
    printable = " ".join(shlex.quote(c) for c in cmd)
    print(f"[ffmpeg] Running:\n{printable}\n")
    subprocess.run(cmd, check=True)


def render_job_to_mp4(
    job: dict[str, Any],
    job_id: str,
    *,
    duration_s: int = 55,
    width: int = 1080,
    height: int = 1920,
    out_dir: str | Path = "tmp/renders",
) -> Path:
    out_dir = Path(out_dir)
    _ensure_dir(out_dir)
    out_path = out_dir / f"{job_id}.mp4"

    assets = job.get("assets") or {}
    clips = assets.get("background_clips") or []
    if not clips or not isinstance(clips, list):
        raise ValueError("Job missing assets.background_clips[0].local_path")

    bg_path = clips[0].get("local_path")
    if not bg_path:
        raise ValueError("Job missing assets.background_clips[0].local_path")

    bg_path = Path(bg_path)
    if not bg_path.exists():
        raise FileNotFoundError(f"Background clip not found: {bg_path}")

    publish = job.get("publish") or {}
    title = publish.get("title") or "Stay focused."

    # Escape for drawtext:
    # - backslash must be escaped
    # - ':' must be escaped
    # - single quote must be escaped
    safe_title = str(title).replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")

    # IMPORTANT: Do NOT set fontfile on Windows in v1.
    # It breaks easily due to ':' in drive letters (C:\...)
    drawtext = (
        "drawtext="
        f"text='{safe_title}':"
        "fontsize=64:"
        "fontcolor=white:"
        "borderw=4:"
        "bordercolor=black@0.6:"
        "x=(w-text_w)/2:"
        "y=(h*0.18):"
        "line_spacing=10"
    )

    vf = (
        f"scale={width}:{height}:force_original_aspect_ratio=increase,"
        f"crop={width}:{height},"
        f"fps=30,"
        f"{drawtext}"
    )

    cmd = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-stream_loop",
        "-1",
        "-i",
        str(bg_path),
        "-t",
        str(duration_s),
        "-vf",
        vf,
        "-an",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-profile:v",
        "high",
        "-level",
        "4.1",
        "-preset",
        "veryfast",
        "-crf",
        "18",
        "-movflags",
        "+faststart",
        str(out_path),
    ]

    _run(cmd)

    if not out_path.exists() or out_path.stat().st_size < 10_000:
        raise RuntimeError(f"Render failed or produced tiny file: {out_path}")

    debug_path = out_dir / f"{job_id}.render_debug.json"
    debug_payload = {
        "job_id": job_id,
        "background": str(bg_path),
        "out_path": str(out_path),
        "duration_s": duration_s,
        "resolution": [width, height],
        "title": title,
        "vf": vf,
        "cmd": cmd,
    }
    debug_path.write_text(json.dumps(debug_payload, indent=2), encoding="utf-8")

    return out_path
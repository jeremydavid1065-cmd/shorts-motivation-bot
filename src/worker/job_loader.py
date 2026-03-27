from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

JOBS_DIR = Path("jobs")
DONE_DIR = JOBS_DIR / "done"


@dataclass(frozen=True)
class JobSummary:
    job_id: str
    job_path: Path
    publish_title: str
    publish_privacyStatus: str
    has_local_background: bool


def _is_real_job_file(path: Path) -> bool:
    """
    Accept: jobs/job_0001.json, jobs/job_abcd.json, etc.
    Reject: jobs/job_schema_v1.json
    """
    if path.suffix.lower() != ".json":
        return False
    name = path.name.lower()
    if not name.startswith("job_"):
        return False
    if "schema" in name:
        return False
    return True


def find_newest_job_file() -> Path | None:
    if not JOBS_DIR.exists():
        return None

    candidates = [p for p in JOBS_DIR.glob("job_*.json") if _is_real_job_file(p)]
    if not candidates:
        return None

    return max(candidates, key=lambda p: p.stat().st_mtime)


def load_job(job_path: Path) -> dict[str, Any]:
    return json.loads(job_path.read_text(encoding="utf-8"))


def get_job_summary(job: dict[str, Any], job_path: Path) -> JobSummary:
    job_id = str(job.get("job_id") or job_path.stem.replace("job_", "", 1))

    publish = job.get("publish") or {}
    title = str(publish.get("title") or "")
    privacy = str(publish.get("privacyStatus") or "")

    assets = job.get("assets") or {}
    clips = assets.get("background_clips") or []
    has_local_bg = False
    if isinstance(clips, list) and clips:
        lp = clips[0].get("local_path")
        has_local_bg = bool(lp)

    return JobSummary(
        job_id=job_id,
        job_path=job_path,
        publish_title=title,
        publish_privacyStatus=privacy,
        has_local_background=has_local_bg,
    )


def mark_job_done(job_path: Path) -> Path:
    DONE_DIR.mkdir(parents=True, exist_ok=True)

    dest = DONE_DIR / job_path.name
    if dest.exists():
        raise FileExistsError(f"Refusing to overwrite existing done job: {dest}")

    shutil.move(str(job_path), str(dest))
    return dest
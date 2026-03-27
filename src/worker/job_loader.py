from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


JOBS_DIR = Path("jobs")


class JobError(Exception):
    pass


@dataclass(frozen=True)
class JobSummary:
    path: Path
    job_id: str
    version: str


def _required_str(d: dict[str, Any], key: str) -> str:
    v = d.get(key)
    if not isinstance(v, str) or not v.strip():
        raise JobError(f"Job missing required string field: {key}")
    return v


def load_job(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise JobError(f"Job file not found: {path}")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise JobError(f"Invalid JSON in {path}: {e}") from e

    if not isinstance(data, dict):
        raise JobError(f"Job JSON must be an object at top level: {path}")

    # Minimal required fields for v1
    _required_str(data, "version")
    _required_str(data, "job_id")

    # These should exist per our schema, but we’ll validate lightly for now
    if "script" not in data:
        raise JobError("Job missing required field: script")
    if "publish" not in data:
        raise JobError("Job missing required field: publish")

    return data


def find_newest_job_file(jobs_dir: Path = JOBS_DIR) -> Path | None:
    if not jobs_dir.exists():
        return None

    candidates = sorted(
        (p for p in jobs_dir.glob("job_*.json") if p.is_file()),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def get_job_summary(job: dict[str, Any], path: Path) -> JobSummary:
    return JobSummary(
        path=path,
        job_id=str(job.get("job_id", "")),
        version=str(job.get("version", "")),
    )
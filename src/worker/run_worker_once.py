from __future__ import annotations
import json
from pathlib import Path

from src.worker.job_loader import JobError, find_newest_job_file, get_job_summary, load_job


def print_plan(job: dict, job_path: Path) -> None:
    summary = get_job_summary(job, job_path)

    print("=== shorts-motivation-bot worker (dry-run) ===")
    print(f"Job file : {summary.path.as_posix()}")
    print(f"Job ID   : {summary.job_id}")
    print(f"Version  : {summary.version}")
    print()

    publish = job.get("publish", {}) if isinstance(job.get("publish"), dict) else {}
    title = publish.get("title", "<missing>")
    visibility = publish.get("visibility", "<missing>")
    print("Publish:")
    print(f"  title      : {title}")
    print(f"  visibility : {visibility}")
    print()

    script = job.get("script", {})
    script_keys = list(script.keys()) if isinstance(script, dict) else []
    print("Script keys:", script_keys)
    print()

    print("Plan:")
    print("  1) Render 1080x1920 video (FFmpeg) [NOT IMPLEMENTED]")
    print("  2) Upload to YouTube via OAuth on this laptop [NOT IMPLEMENTED]")
    print("  3) Mark job done (move/rename) [NOT IMPLEMENTED]")
    print()
    print("Full job JSON (preview):")
    print(json.dumps(job, indent=2)[:1500])


def main() -> int:
    job_path = find_newest_job_file()
    if job_path is None:
        print("No job files found in /jobs (expected jobs/job_*.json).")
        return 0

    try:
        job = load_job(job_path)
    except JobError as e:
        print(f"JOB ERROR: {e}")
        print(f"Offending file: {job_path}")
        return 2

    print_plan(job, job_path)
    return 0

if __name__ == "__main__":

    raise SystemExit(main())
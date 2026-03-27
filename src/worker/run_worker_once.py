from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.rendering.ffmpeg_renderer import render_job_to_mp4
from src.worker.job_loader import find_newest_job_file, load_job, mark_job_done


def _job_id_from_path(job_path: Path) -> str:
    # jobs/job_0002.json -> 0002
    stem = job_path.stem  # job_0002
    if stem.startswith("job_"):
        return stem.replace("job_", "", 1)
    return stem


def main() -> int:
    parser = argparse.ArgumentParser(description="Process the newest job once (dry-run by default).")
    parser.add_argument(
        "--mark-done",
        action="store_true",
        help="Move processed job JSON into jobs/done/ (ONLY if you really processed it).",
    )
    parser.add_argument(
        "--render",
        action="store_true",
        help="Render an MP4 for the newest job into tmp/renders/<job_id>.mp4",
    )
    args = parser.parse_args()

    job_path = find_newest_job_file()
    if job_path is None:
        print("No job files found in jobs/. Nothing to do.")
        return 0

    job = load_job(job_path)
    job_id = _job_id_from_path(job_path)

    print("=== Newest job ===")
    print(f"job_file: {job_path}")
    print(f"job_id: {job_id}")

    print("\n=== Job JSON preview ===")
    job_pretty = json.dumps(job, indent=2)
    print(job_pretty[:4000])
    if len(job_pretty) > 4000:
        print("... (truncated)")

    if not args.render and not args.mark_done:
        print("\nDry-run only (no --render, no --mark-done). No changes made.")
        return 0

    if args.render:
        print("\n=== Rendering ===")
        rendered_path = render_job_to_mp4(job, job_id)
        print(f"Rendered MP4: {rendered_path}")

    if args.mark_done:
        print("\n=== Marking job done ===")
        mark_job_done(job_path)
        print(f"Moved job to done: {job_path.name}")

    print("\nDone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
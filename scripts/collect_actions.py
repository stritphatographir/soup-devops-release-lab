"""Save real run/job/log evidence and check that failures expose the intended fault."""

import argparse
import datetime as dt
import json
import subprocess
from pathlib import Path

REPO = "stritphatographir/soup-devops-release-lab"
REQUIRED = {
    "python310": ("ubuntu-latest", "3.10", "No module named 'tomllib'"),
    "windows": ("windows-latest", "3.12", "No module named 'pwd'"),
    "missing-data": ("ubuntu-latest", "3.12", "defaults.json"),
    "entrypoint": ("ubuntu-latest", "3.12", "missing_main"),
}


def gh(*arguments: str) -> str:
    return subprocess.check_output(
        ["gh", *arguments], text=True, encoding="utf-8", errors="replace",
    )


def collect(plan: list[dict], output: Path) -> None:
    output.mkdir(parents=True, exist_ok=False)
    snapshots = []
    accepted = True
    for item in plan:
        run_id, bug, pipeline = item["run_id"], item["bug"], item["pipeline"]
        run = json.loads(gh("api", f"repos/{REPO}/actions/runs/{run_id}"))
        jobs = json.loads(gh("api", f"repos/{REPO}/actions/runs/{run_id}/jobs?per_page=100"))
        row = {key: run[key] for key in (
            "id", "html_url", "head_sha", "status", "conclusion", "created_at", "updated_at",
        )}
        row.update(bug=bug, pipeline=pipeline, jobs=jobs["jobs"], accepted=False)
        if run["status"] == "completed" and jobs["total_count"]:
            log = gh("run", "view", str(run_id), "--repo", REPO, "--log")
            (output / f"{bug}-{pipeline}-{run_id}.txt").write_text(log, encoding="utf-8")
            if pipeline == "naive":
                row["accepted"] = run["conclusion"] == "success"
            elif bug == "fixed":
                consumers = [job for job in jobs["jobs"] if "consumers (" in job["name"]]
                row["accepted"] = (
                    run["conclusion"] == "success" and len(consumers) == 15
                    and all(job["conclusion"] == "success" for job in jobs["jobs"])
                )
            else:
                os_name, python, signature = REQUIRED[bug]
                rejecting = [job for job in jobs["jobs"] if "consumers (" in job["name"]
                             and os_name in job["name"] and python in job["name"]
                             and job["conclusion"] == "failure"]
                rejecting_names = {job["name"] for job in rejecting}
                consumer_log = "\n".join(
                    line for line in log.splitlines()
                    if line.split("\t", 1)[0] in rejecting_names
                )
                row["matched_signature"] = signature if signature in consumer_log else None
                row["rejecting_jobs"] = sorted(rejecting_names)
                row["accepted"] = bool(
                    run["conclusion"] == "failure" and rejecting and signature in consumer_log
                )
        snapshots.append(row)
        accepted = accepted and row["accepted"]
        print(f"{bug}/{pipeline}: {run['conclusion'] or run['status']}; accepted={row['accepted']}")
    summary = {
        "observed_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "repository": REPO, "all_expected_outcomes_observed": accepted, "runs": snapshots,
    }
    (output / "runs.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    if not accepted:
        raise SystemExit(
            "Some runs are pending or did not establish the expected outcome; see snapshot"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    collect(json.loads(args.plan.read_text(encoding="utf-8")), args.out)

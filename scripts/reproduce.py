"""Preserve genuine naive passes and consumer failures; never disguise a CI run."""

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
from pathlib import Path

from inject_bug import materialize

ROOT = Path(__file__).resolve().parents[1]
PY310 = "python:3.10-slim@sha256:6ff506466f8b1e981719b468cc0023b8ef000b983cdec0eafe119d01f379e31d"
SIGNATURES = {
    "python310": "No module named 'tomllib'",
    "windows": "No module named 'pwd'",
    "missing-data": "defaults.json",
    "entrypoint": "missing_main",
}


def record(command: list[str], log: Path) -> tuple[int, str]:
    print(f"Running {log.stem} ...", flush=True)
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    result = subprocess.run(
        command, cwd=ROOT, env=env, text=True, encoding="utf-8", errors="replace",
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=900,
    )
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(
        "$ " + subprocess.list2cmdline(command) + "\n\n" + result.stdout
        + f"\nExit code: {result.returncode}\n", encoding="utf-8",
    )
    shown = log.relative_to(ROOT) if log.is_relative_to(ROOT) else log
    print(f"  exit={result.returncode}; evidence={shown}", flush=True)
    return result.returncode, result.stdout


def require_pass(result: tuple[int, str]) -> None:
    if result[0] != 0:
        raise RuntimeError(
            f"an unexpected infrastructure/build failure occurred:\n{result[1][-6000:]}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if os.name != "nt":
        raise RuntimeError("full local reproduction requires Windows plus Linux Docker")
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = (args.out or ROOT / "evidence/local" / f"reproduction-{stamp}").resolve()
    output.mkdir(parents=True, exist_ok=False)
    workspace = ROOT / "tmp" / f"reproduce-{stamp}"
    workspace.mkdir(parents=True)
    for minor, extra in (("3.12", []), ("3.10", ["--build-arg", f"PYTHON_IMAGE={PY310}"])):
        require_pass(record(
            ["docker", "build", "--target", "ci", "--tag", f"soup-lab-ci:{minor}",
             *extra, "."], output / f"image-{minor}.txt",
        ))

    def docker(minor: str, fixture: Path, *command: str) -> list[str]:
        return [
            "docker", "run", "--rm", "-e", "PYTHONUTF8=1",
            "--mount", f"type=bind,source={ROOT},target=/project,readonly",
            "--mount", f"type=bind,source={fixture},target=/candidate",
            "--mount", f"type=bind,source={workspace},target=/results",
            f"soup-lab-ci:{minor}", *command,
        ]

    summary = {"executed_at_utc": stamp, "kind": "local executions, not GitHub Actions",
               "source_state": "working tree; inspect Git history for the submitted revision",
               "bugs": {}, "fixed": []}
    for bug, signature in SIGNATURES.items():
        fixture = workspace / bug
        materialize(ROOT, fixture, bug)
        naive = record(
            docker("3.12", fixture, "python", "scripts/naive_check.py", "--source", "/candidate"),
            output / f"{bug}-naive.txt",
        )
        require_pass(naive)
        require_pass(record(
            docker("3.12", fixture, "python", "scripts/build_release.py", "--source", "/candidate",
                   "--out", f"/results/{bug}-release"), output / f"{bug}-build.txt",
        ))
        if bug == "windows":
            command = [sys.executable, "scripts/smoke_artifact.py", "--bundle",
                       str(workspace / f"{bug}-release"), "--kind", "wheel"]
        else:
            command = docker(
                "3.10" if bug == "python310" else "3.12", fixture,
                "python", "scripts/smoke_artifact.py", "--bundle", f"/results/{bug}-release",
                "--kind", "wheel",
            )
        hardened = record(command, output / f"{bug}-hardened.txt")
        if hardened[0] == 0 or signature not in hardened[1]:
            raise RuntimeError(
                f"{bug}: did not fail for the expected reason; inspect preserved log"
            )
        summary["bugs"][bug] = {
            "naive_exit": naive[0], "build_exit": 0, "consumer_exit": hardened[0],
            "matched_failure_signature": signature,
            "platform": "Windows" if bug == "windows" else "Linux Docker",
        }
        (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")

    fixture = workspace / "fixed"
    materialize(ROOT, fixture, "fixed")
    require_pass(record(
        docker("3.12", fixture, "python", "scripts/build_release.py", "--source", "/candidate",
               "--out", "/results/fixed-release"), output / "fixed-build.txt",
    ))
    for minor in ("3.10", "3.12", "windows"):
        for kind in ("wheel", "sdist"):
            if minor == "windows":
                command = [sys.executable, "scripts/smoke_artifact.py", "--bundle",
                           str(workspace / "fixed-release"), "--kind", kind]
            else:
                command = docker(minor, fixture, "python", "scripts/smoke_artifact.py",
                                 "--bundle", "/results/fixed-release", "--kind", kind)
            require_pass(record(command, output / f"fixed-{minor}-{kind}.txt"))
            summary["fixed"].append({"environment": minor, "kind": kind, "exit": 0})
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (output / "bundle-location.txt").write_text(str(workspace / "fixed-release") + "\n")
    print("Four genuine consumer failures and six fixed consumer passes preserved.")


if __name__ == "__main__":
    main()

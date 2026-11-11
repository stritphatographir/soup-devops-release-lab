"""Generate and validate the matrix, including the environment each fault needs."""

import argparse
import itertools
import json
from pathlib import Path

from inject_bug import BUGS

PYTHONS = ("3.10", "3.11", "3.12", "3.13", "3.14")
OSES = ("ubuntu-latest", "windows-latest", "macos-latest")
BUG_LEGS = {
    "python310": ("ubuntu-latest", "3.10"),
    "windows": ("windows-latest", "3.12"),
    "missing-data": ("ubuntu-latest", "3.12"),
    "entrypoint": ("ubuntu-latest", "3.12"),
}


def validate_plan(matrix: dict, bug: str) -> None:
    if set(BUG_LEGS) != set(BUGS) - {"fixed"}:
        raise ValueError("every fixture must declare the environment that exposes it")
    if bug not in BUGS:
        raise ValueError(f"unknown fault: {bug}")
    legs = matrix["include"]
    actual = {(leg["os"], leg["python"]) for leg in legs}
    full = set(itertools.product(OSES, PYTHONS))
    if not actual or len(actual) != len(legs) or not actual <= full:
        raise ValueError("matrix has empty, duplicate, or unsupported consumer legs")
    if bug == "fixed" and actual != full:
        raise ValueError("fixed candidate must cover the full support contract")
    if bug != "fixed" and BUG_LEGS[bug] not in actual:
        raise ValueError(f"matrix cannot expose {bug}: missing {BUG_LEGS[bug]}")


def plan(bug: str) -> dict:
    legs = itertools.product(OSES, PYTHONS) if bug == "fixed" else sorted(set(BUG_LEGS.values()))
    matrix = {"include": [{"os": os_name, "python": python} for os_name, python in legs]}
    validate_plan(matrix, bug)
    return matrix


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bug", choices=BUGS, required=True)
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args()
    data = json.dumps(plan(args.bug), separators=(",", ":"))
    if args.github_output:
        with args.github_output.open("a", encoding="utf-8") as stream:
            stream.write(f"matrix={data}\n")
    print(data)

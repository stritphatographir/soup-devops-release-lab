"""Read a TOML service configuration and print a deterministic JSON report."""

import argparse
import json
import sys
from importlib import resources
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10 is part of the supported contract.
    import tomli as tomllib

from . import __version__
from .core import validate_name, validate_workers


def inspect_configuration(path: Path) -> dict[str, str | int]:
    defaults = json.loads(
        resources.files("soup_release_lab").joinpath("data/defaults.json").read_text("utf-8")
    )
    with path.open("rb") as stream:
        configuration = tomllib.load(stream)
    service = configuration.get("service")
    if not isinstance(service, dict):
        raise ValueError("a [service] table is required")
    return {
        "name": validate_name(service.get("name")),
        "workers": validate_workers(service.get("workers", 1), defaults["max_workers"]),
        "profile": defaults["profile"],
        "schema": defaults["schema"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="soup-check", description=__doc__)
    parser.add_argument("--version", action="version", version=f"soup-check {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)
    inspect = commands.add_parser("inspect", help="validate a TOML configuration")
    inspect.add_argument("configuration", type=Path)
    args = parser.parse_args(argv)
    try:
        report = inspect_configuration(args.configuration)
    except (OSError, ValueError) as error:
        print(f"soup-check: {error}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=True, sort_keys=True))
    return 0


"""Copy the project and introduce exactly one fault; never edit the checkout."""

import argparse
import shutil
from pathlib import Path

BUGS = ("fixed", "python310", "windows", "missing-data", "entrypoint")
IGNORES = (
    ".git", ".venv", ".tools", "tmp", "dist", "build", "*.egg-info", "__pycache__",
    ".pytest_cache", ".ruff_cache", ".coverage", "evidence", "output", "htmlcov",
)


def replace_once(path: Path, before: str, after: str) -> None:
    text = path.read_text(encoding="utf-8")
    if text.count(before) != 1:
        raise ValueError(f"fixture drift: expected exactly one match in {path.name}")
    path.write_text(text.replace(before, after), encoding="utf-8")


def materialize(source: Path, destination: Path, bug: str) -> None:
    source, destination = source.resolve(), destination.resolve()
    if bug not in BUGS:
        raise ValueError(f"unknown bug: {bug}")
    if destination == source or source.is_relative_to(destination):
        raise ValueError("destination must not contain the source checkout")
    if destination.is_relative_to(source) and not destination.is_relative_to(source / "tmp"):
        raise ValueError("inside the checkout, fixtures must live under tmp/")
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns(*IGNORES))
    if bug == "fixed":
        return
    replace_once(destination / "pyproject.toml", 'version = "0.9.4"', 'version = "0.9.3"')
    replace_once(
        destination / "src/soup_release_lab/__init__.py",
        '__version__ = "0.9.4"', '__version__ = "0.9.3"',
    )
    cli = destination / "src/soup_release_lab/cli.py"
    if bug == "python310":
        replace_once(
            cli,
            'try:\n    import tomllib\n'
            'except ModuleNotFoundError:  # Python 3.10 is part of the supported contract.\n'
            '    import tomli as tomllib',
            "",
        )
        replace_once(cli, "import sys\n", "import sys\nimport tomllib\n")
    elif bug == "windows":
        replace_once(
            cli, "from pathlib import Path\n",
            "from pathlib import Path\nfrom pwd import getpwuid as getpwuid\n",
        )
    elif bug == "missing-data":
        replace_once(destination / "pyproject.toml", '["data/*.json"]', "[]")
    elif bug == "entrypoint":
        replace_once(destination / "pyproject.toml", 'cli:main"', 'cli:missing_main"')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bug", choices=BUGS, required=True)
    parser.add_argument("--source", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    materialize(args.source, args.destination, args.bug)
    print(f"Created {args.bug} fixture at {args.destination}")


if __name__ == "__main__":
    main()


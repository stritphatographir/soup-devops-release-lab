"""Intentionally weak CI: editable install and library-only tests on Linux 3.12."""

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path.cwd())
    args = parser.parse_args()
    subprocess.run(
        [sys.executable, "-m", "pip", "--isolated", "install", "--no-deps",
         "--no-build-isolation", "-e", str(args.source.resolve())], check=True,
    )
    subprocess.run(
        [sys.executable, "-m", "pytest", "tests/naive", "-q"],
        cwd=args.source, check=True,
    )


if __name__ == "__main__":
    main()

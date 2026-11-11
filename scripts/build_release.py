"""Build once, from the sdist, with the hash-locked toolchain already installed."""

import argparse
import os
import subprocess
import sys
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

from bundle import write_manifest


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path.cwd())
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--source-sha",
                        default=os.environ.get("GITHUB_SHA") or "local-uncommitted",
                        help="omit for a local build, never pass it empty")
    parser.add_argument("--tag", help="omit outside a release, never pass it empty")
    args = parser.parse_args(argv)
    if not args.source_sha:
        parser.error("--source-sha needs a commit; omit it for a local build")
    if args.tag == "":
        parser.error("--tag needs a release tag; omit it outside a release")
    return args


def main() -> None:
    args = parse_args()
    source, output = args.source.resolve(), args.out.resolve()
    if output.exists():
        raise ValueError(f"output already exists; refusing stale artifacts: {output}")
    with (source / "pyproject.toml").open("rb") as stream:
        version = tomllib.load(stream)["project"]["version"]
    output.mkdir(parents=True)
    env = os.environ.copy()
    env["SOURCE_DATE_EPOCH"] = "1700000000"
    subprocess.run(
        [sys.executable, "-m", "build", "--no-isolation", "--outdir",
         str(output / "dist"), str(source)],
        env=env, check=True,
    )
    manifest = write_manifest(output, version, args.source_sha, args.tag)
    print(f"Bound {len(manifest['files'])} distributions to {args.source_sha}; version={version}")


if __name__ == "__main__":
    main()

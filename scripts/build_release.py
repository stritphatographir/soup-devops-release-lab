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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path.cwd())
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--source-sha", default=os.environ.get("GITHUB_SHA", "local-uncommitted"))
    parser.add_argument("--tag", default="")
    args = parser.parse_args()
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


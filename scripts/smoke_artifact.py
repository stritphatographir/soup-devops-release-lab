"""Exercise installed distributions in a fresh venv outside the source checkout."""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import venv
from pathlib import Path

from bundle import verify_manifest

ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str], cwd: Path, expected: int = 0) -> str:
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env.pop("PYTHONHOME", None)
    env["PIP_NO_CACHE_DIR"] = "1"
    result = subprocess.run(command, cwd=cwd, env=env, text=True, capture_output=True)
    print(f"$ {' '.join(command)}\n{result.stdout}{result.stderr}", flush=True)
    if result.returncode != expected:
        raise RuntimeError(f"command returned {result.returncode}, expected {expected}")
    return result.stdout


def smoke(bundle: Path, kind: str, runtime_lock: Path, build_lock: Path) -> None:
    bundle = bundle.resolve()
    manifest = verify_manifest(bundle)
    suffix = ".whl" if kind == "wheel" else ".tar.gz"
    artifact = next((bundle / "dist").glob(f"*{suffix}"))
    with tempfile.TemporaryDirectory(prefix="soup consumer ") as temp:
        working = Path(temp)
        environment = working / "venv"
        venv.EnvBuilder(with_pip=True, clear=False).create(environment)
        binary = environment / ("Scripts" if os.name == "nt" else "bin")
        python = binary / ("python.exe" if os.name == "nt" else "python")
        cli = binary / ("soup-check.exe" if os.name == "nt" else "soup-check")
        pip = [str(python), "-I", "-m", "pip", "--isolated", "--disable-pip-version-check"]
        install = [*pip, "install", "--no-cache-dir", "--index-url", "https://pypi.org/simple",
                   "--require-hashes", "--only-binary=:all:"]
        run([*install, "-r", str(runtime_lock.resolve())], working)
        if kind == "sdist":
            run([*install, "-r", str(build_lock.resolve())], working)
        run([*pip, "install", "--no-deps", "--no-index", "--no-build-isolation", str(artifact)],
            working)
        run([*pip, "check"], working)
        installed = run(
            [str(python), "-I", "-c", "import soup_release_lab; print(soup_release_lab.__file__)"],
            working,
        ).strip()
        if not Path(installed).resolve().is_relative_to(environment.resolve()):
            raise ValueError("import escaped the consumer virtual environment")
        expected_version = f"soup-check {manifest['version']}"
        for command in ([str(cli), "--version"],
                        [str(python), "-I", "-m", "soup_release_lab", "--version"]):
            if run(command, working).strip() != expected_version:
                raise ValueError("installed CLI version differs from distribution metadata")
        run([str(cli), "--help"], working)
        config = working / "service caf\u00e9 with spaces.toml"
        config.write_text('[service]\nname = "caf\u00e9"\nworkers = 3\n', encoding="utf-8")
        report = json.loads(run([str(cli), "inspect", str(config)], working))
        if report != {"name": "caf\u00e9", "workers": 3, "profile": "safe", "schema": 1}:
            raise ValueError(f"unexpected consumer result: {report}")
        config.write_text('[service]\nname="example"\nworkers=0\n', encoding="utf-8")
        run([str(cli), "inspect", str(config)], working, expected=2)
        run([str(cli), "inspect", str(working / "missing.toml")], working, expected=2)
    print(f"PASS: clean {kind} consumer on {sys.platform} / Python {sys.version.split()[0]}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--kind", choices=("wheel", "sdist"), required=True)
    parser.add_argument("--runtime-lock", type=Path, default=ROOT / "requirements/runtime.lock")
    parser.add_argument("--build-lock", type=Path, default=ROOT / "requirements/build.lock")
    args = parser.parse_args()
    smoke(args.bundle, args.kind, args.runtime_lock, args.build_lock)

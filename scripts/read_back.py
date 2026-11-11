"""Prove that TestPyPI serves exactly the distributions that passed the gates."""

import argparse
import hashlib
import json
import shutil
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from bundle import verify_manifest
from smoke_artifact import ROOT, smoke


def public_files_ready(entries: list[dict], expected: set[str]) -> bool:
    names = {entry["filename"] for entry in entries}
    if len(names) != len(entries) or names - expected:
        raise ValueError("unexpected or duplicate public distribution; refusing acceptance")
    return names == expected


def read_back(bundle: Path, output: Path) -> None:
    manifest = verify_manifest(bundle)
    url = f"https://test.pypi.org/pypi/{manifest['project']}/{manifest['version']}/json"
    for attempt in range(10):
        try:
            with urllib.request.urlopen(url, timeout=20) as response:
                public = json.load(response)
            if public_files_ready(public["urls"], set(manifest["files"])):
                break
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
            if attempt == 9:
                raise
        time.sleep(6)
    else:
        raise RuntimeError("TestPyPI did not expose both distributions before the deadline")
    output.mkdir(parents=True, exist_ok=False)
    (output / "dist").mkdir()
    shutil.copyfile(bundle / "manifest.json", output / "manifest.json")
    for item in public["urls"]:
        name = item["filename"]
        if name not in manifest["files"]:
            continue
        if urllib.parse.urlparse(item["url"]).scheme != "https":
            raise ValueError("refusing an insecure artifact URL")
        with urllib.request.urlopen(item["url"], timeout=30) as response:
            data = response.read()
        if hashlib.sha256(data).hexdigest() != manifest["files"][name]:
            raise ValueError(f"TestPyPI served different bytes: {name}")
        (output / "dist" / name).write_bytes(data)
    verify_manifest(output)
    for kind in ("wheel", "sdist"):
        smoke(output, kind, ROOT / "requirements/runtime.lock", ROOT / "requirements/build.lock")
    print("PASS: downloaded TestPyPI bytes match the tested release")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    read_back(args.bundle.resolve(), args.out.resolve())

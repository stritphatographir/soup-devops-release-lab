"""Validate distribution identity and bind immutable bytes to their source commit."""

import argparse
import hashlib
import json
import re
import tarfile
import zipfile
from email.parser import BytesParser
from pathlib import Path

PROJECT = "soup-release-lab-amirt"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_tag(version: str, tag: str | None) -> None:
    if tag and (not re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+", tag) or tag != f"v{version}"):
        raise ValueError(f"tag {tag!r} does not match artifact version {version!r}")


def metadata(path: Path) -> tuple[str, str]:
    if path.suffix == ".whl":
        with zipfile.ZipFile(path) as archive:
            names = [name for name in archive.namelist() if name.endswith(".dist-info/METADATA")]
            if len(names) != 1:
                raise ValueError("wheel must have one METADATA file")
            raw = archive.read(names[0])
    else:
        with tarfile.open(path, "r:gz") as archive:
            names = [m for m in archive.getmembers() if m.name.count("/") == 1
                     and m.name.endswith("/PKG-INFO")]
            if len(names) != 1:
                raise ValueError("sdist must have one top-level PKG-INFO")
            stream = archive.extractfile(names[0])
            if stream is None:
                raise ValueError("missing sdist metadata")
            raw = stream.read()
    message = BytesParser().parsebytes(raw)
    return re.sub(r"[-_.]+", "-", str(message["Name"])).lower(), str(message["Version"])


def write_manifest(root: Path, version: str, source_sha: str, tag: str | None = None) -> dict:
    require_tag(version, tag)
    files = sorted((root / "dist").iterdir())
    if len(files) != 2 or sum(p.suffix == ".whl" for p in files) != 1 or sum(
        p.name.endswith(".tar.gz") for p in files
    ) != 1:
        raise ValueError("release must contain exactly one wheel and one sdist")
    for path in files:
        if metadata(path) != (PROJECT, version):
            raise ValueError(f"distribution identity mismatch: {path.name}")
    manifest = {
        "schema": 1, "project": PROJECT, "version": version, "source_sha": source_sha,
        "files": {p.name: digest(p) for p in files},
    }
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def verify_manifest(root: Path, source_sha: str | None = None, tag: str | None = None) -> dict:
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("schema") != 1 or manifest.get("project") != PROJECT:
        raise ValueError("unknown manifest format or project")
    if source_sha and manifest["source_sha"] != source_sha:
        raise ValueError("artifact source SHA mismatch")
    require_tag(manifest["version"], tag)
    names = manifest["files"]
    if set(names) != {p.name for p in (root / "dist").iterdir()}:
        raise ValueError("unexpected or missing release file")
    if len(names) != 2 or sum(n.endswith(".whl") for n in names) != 1 or sum(
        n.endswith(".tar.gz") for n in names
    ) != 1:
        raise ValueError("manifest must name exactly one wheel and one sdist")
    for name, expected in names.items():
        if Path(name).name != name or digest(root / "dist" / name) != expected:
            raise ValueError(f"artifact checksum mismatch: {name}")
        if metadata(root / "dist" / name) != (PROJECT, manifest["version"]):
            raise ValueError(f"artifact metadata mismatch: {name}")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--source-sha")
    parser.add_argument("--tag")
    args = parser.parse_args()
    print(json.dumps(verify_manifest(args.bundle, args.source_sha, args.tag), indent=2))

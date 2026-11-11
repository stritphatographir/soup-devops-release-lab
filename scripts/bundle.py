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
DISTRIBUTION = PROJECT.replace("-", "_")
TAG_SHAPE = re.compile(r"v[0-9]+\.[0-9]+\.[0-9]+")
VERSION_SHAPE = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+")
# The consumer venv installs requirements/runtime.lock before the artifact, so a
# dropped dependency still looks satisfied there. Only published metadata can
# carry the project's single dependency, so its exact form is pinned here.
REQUIRES_PYTHON = ">=3.10,<3.15"
REQUIRES_DIST = ('tomli==2.2.1; python_version < "3.11"',)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize(value: str) -> str:
    """Marker text as core metadata spells it: one space per gap, double quotes."""
    return re.sub(r"\s+", " ", value.replace("'", '"')).strip()


def specifiers(value: str) -> str:
    """Requires-Python in a stable order; setuptools reorders specifiers."""
    return ",".join(sorted(part for part in (normalize(x) for x in value.split(",")) if part))


def published_names(version: str) -> set[str]:
    """The wheel and sdist this project publishes for one version.

    Comparing the manifest and the directory against this set is also the
    distribution filename check: a renamed or platform-tagged file fails here.
    """
    return {
        f"{DISTRIBUTION}-{version}-py3-none-any.whl",
        f"{DISTRIBUTION}-{version}.tar.gz",
    }


def require_tag(version: str, tag: str | None) -> None:
    """None is a branch or local build; an empty string is a lost release input."""
    if tag is None:
        return
    if not tag:
        raise ValueError("tag was supplied empty; omit it outside a release")
    if not TAG_SHAPE.fullmatch(tag) or tag != f"v{version}":
        raise ValueError(f"tag {tag!r} does not match artifact version {version!r}")


def require_supplied(value: str | None, label: str) -> None:
    """A flag passed with no value lost the identity; it did not abstain from it."""
    if value is not None and not value:
        raise ValueError(f"{label} was supplied empty")


def metadata(path: Path) -> tuple[str, str, str, tuple[str, ...]]:
    """(name, version, requires-python, requires-dist) as the distribution declares them."""
    if path.suffix == ".whl":
        with zipfile.ZipFile(path) as archive:
            names = [name for name in archive.namelist() if name.endswith(".dist-info/METADATA")]
            if len(names) != 1:
                raise ValueError("wheel must have one METADATA file")
            raw = archive.read(names[0])
    else:
        with tarfile.open(path, "r:gz") as archive:
            members = [m for m in archive.getmembers()
                       if m.name.count("/") == 1 and m.name.endswith("/PKG-INFO")]
            if len(members) != 1:
                raise ValueError("sdist must have one top-level PKG-INFO")
            stream = archive.extractfile(members[0])
            if stream is None:
                raise ValueError("missing sdist metadata")
            raw = stream.read()
    message = BytesParser().parsebytes(raw)
    name = re.sub(r"[-_.]+", "-", str(message["Name"] or "")).lower()
    version = str(message["Version"] or "")
    requires_python = specifiers(str(message["Requires-Python"] or ""))
    requires_dist = tuple(sorted(normalize(x) for x in message.get_all("Requires-Dist", [])))
    return name, version, requires_python, requires_dist


def require_identity(path: Path, version: str, mismatch: str) -> None:
    """The identity a distribution declares inside its own metadata."""
    name, declared, requires_python, requires_dist = metadata(path)
    if (name, declared) != (PROJECT, version):
        raise ValueError(f"{mismatch}: {path.name}")
    if requires_python != specifiers(REQUIRES_PYTHON):
        raise ValueError(f"Requires-Python mismatch: {path.name}")
    if requires_dist != tuple(sorted(normalize(x) for x in REQUIRES_DIST)):
        raise ValueError(f"Requires-Dist mismatch: {path.name}")


def write_manifest(root: Path, version: str, source_sha: str, tag: str | None = None) -> dict:
    require_tag(version, tag)
    require_supplied(source_sha, "source SHA")
    files = sorted((root / "dist").iterdir())
    if {path.name for path in files} != published_names(version):
        raise ValueError("release must contain exactly one wheel and one sdist")
    for path in files:
        require_identity(path, version, "distribution identity mismatch")
    manifest = {
        "schema": 1, "project": PROJECT, "version": version, "source_sha": source_sha,
        "files": {p.name: digest(p) for p in files},
    }
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def verify_manifest(root: Path, source_sha: str | None = None, tag: str | None = None) -> dict:
    require_supplied(source_sha, "source SHA")
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("schema") != 1 or manifest.get("project") != PROJECT:
        raise ValueError("unknown manifest format or project")
    if source_sha and manifest["source_sha"] != source_sha:
        raise ValueError("artifact source SHA mismatch")
    version = str(manifest["version"])
    require_tag(version, tag)
    names = manifest["files"]
    if set(names) != {p.name for p in (root / "dist").iterdir()}:
        raise ValueError("unexpected or missing release file")
    if set(names) != published_names(version):
        raise ValueError("manifest must name the published wheel and sdist")
    for name, expected in names.items():
        if Path(name).name != name:
            raise ValueError(f"unsafe artifact name: {name}")
        if digest(root / "dist" / name) != expected:
            raise ValueError(f"artifact checksum mismatch: {name}")
        require_identity(root / "dist" / name, version, "artifact metadata mismatch")
    return manifest


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--source-sha", help="omit for a local build, never pass it empty")
    parser.add_argument("--tag", help="omit outside a release, never pass it empty")
    args = parser.parse_args(argv)
    if args.source_sha == "":
        parser.error("--source-sha needs a commit; omit it for a local build")
    if args.tag == "":
        parser.error("--tag needs a release tag; omit it outside a release")
    return args


if __name__ == "__main__":
    options = parse_args()
    result = verify_manifest(options.bundle, options.source_sha, options.tag)
    print(json.dumps(result, indent=2))

"""Synthetic one-wheel-plus-one-sdist bundles, spelled the way setuptools spells them."""

import hashlib
import io
import json
import tarfile
import zipfile
from pathlib import Path

NAME = "soup-release-lab-amirt"
DISTRIBUTION = "soup_release_lab_amirt"
VERSION = "0.9.4"
SHA = "a" * 40
TAG = "v0.9.4"
# Setuptools writes Requires-Python with the specifiers reordered; the guards
# have to agree with the real bytes, not with pyproject.toml's spelling.
REQUIRES_PYTHON = "<3.15,>=3.10"
REQUIRES_DIST = ('tomli==2.2.1; python_version < "3.11"',)


def metadata_text(
    *,
    name: str = NAME,
    version: str = VERSION,
    requires_python: str | None = REQUIRES_PYTHON,
    requires_dist: tuple[str, ...] = REQUIRES_DIST,
) -> str:
    text = f"Metadata-Version: 2.4\nName: {name}\nVersion: {version}\n"
    if requires_python is not None:
        text += f"Requires-Python: {requires_python}\n"
    return text + "".join(f"Requires-Dist: {item}\n" for item in requires_dist)


def write_wheel(path: Path, metadata: str, version: str = VERSION) -> None:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        prefix = f"{DISTRIBUTION}-{version}"
        archive.writestr(f"{prefix}.dist-info/METADATA", metadata)
        archive.writestr(f"{prefix}.dist-info/WHEEL", "Wheel-Version: 1.0\n")
        archive.writestr("soup_release_lab/__init__.py", f'__version__ = "{version}"\n')


def write_sdist(path: Path, metadata: str, version: str = VERSION) -> None:
    payload = metadata.encode("utf-8")
    with tarfile.open(path, "w:gz") as archive:
        for name, body in (
            (f"{DISTRIBUTION}-{version}/PKG-INFO", payload),
            (f"{DISTRIBUTION}-{version}/pyproject.toml", b"[project]\nname = 'x'\n"),
        ):
            entry = tarfile.TarInfo(name)
            entry.size = len(body)
            archive.addfile(entry, io.BytesIO(body))


def build_bundle(
    root: Path,
    *,
    version: str = VERSION,
    source_sha: str = SHA,
    wheel_name: str | None = None,
    sdist_name: str | None = None,
    wheel_meta: str | None = None,
    sdist_meta: str | None = None,
    extra: tuple[str, ...] = (),
) -> Path:
    """Write a bundle whose manifest hashes the bytes that are actually on disk."""
    dist = root / "dist"
    dist.mkdir(parents=True)
    wheel = wheel_name or f"{DISTRIBUTION}-{version}-py3-none-any.whl"
    sdist = sdist_name or f"{DISTRIBUTION}-{version}.tar.gz"
    write_wheel(dist / wheel, wheel_meta or metadata_text(version=version), version)
    write_sdist(dist / sdist, sdist_meta or metadata_text(version=version), version)
    for name in extra:
        (dist / name).write_bytes(b"an unexpected distribution\n")
    # Extras stay out of the manifest: they joined the artifact after it was built.
    files = {name: hashlib.sha256((dist / name).read_bytes()).hexdigest()
             for name in (wheel, sdist)}
    manifest = {"schema": 1, "project": NAME, "version": version, "source_sha": source_sha,
                "files": files}
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return root

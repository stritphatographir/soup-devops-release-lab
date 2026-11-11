import io
import json
import tarfile
import zipfile

import pytest
from bundle import require_tag, verify_manifest, write_manifest
from inject_bug import materialize


def make_bundle(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    data = b"Name: soup-release-lab-amirt\nVersion: 0.9.4\n"
    with zipfile.ZipFile(dist / "example.whl", "w") as archive:
        archive.writestr("example-0.9.4.dist-info/METADATA", data)
    with tarfile.open(dist / "example.tar.gz", "w:gz") as archive:
        entry = tarfile.TarInfo("example/PKG-INFO")
        entry.size = len(data)
        archive.addfile(entry, io.BytesIO(data))
    write_manifest(tmp_path, "0.9.4", "a" * 40, "v0.9.4")
    return tmp_path


def test_bundle_identity(tmp_path):
    root = make_bundle(tmp_path)
    assert verify_manifest(root, "a" * 40, "v0.9.4")["version"] == "0.9.4"


def test_stale_artifact_rejected(tmp_path):
    root = make_bundle(tmp_path)
    with pytest.raises(ValueError, match="source SHA"):
        verify_manifest(root, "b" * 40)


def test_tampered_bytes_rejected(tmp_path):
    root = make_bundle(tmp_path)
    (root / "dist/example.whl").write_bytes(b"different bytes")
    with pytest.raises(ValueError, match="checksum"):
        verify_manifest(root)


def test_unexpected_file_rejected(tmp_path):
    root = make_bundle(tmp_path)
    (root / "dist/stale.whl").write_bytes(b"extra")
    with pytest.raises(ValueError, match="unexpected"):
        verify_manifest(root)


def test_manifest_path_traversal_rejected(tmp_path):
    root = make_bundle(tmp_path)
    manifest_path = root / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["files"]["../outside.whl"] = manifest["files"].pop("example.whl")
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError):
        verify_manifest(root)


@pytest.mark.parametrize("tag", ["v0.9.3", "0.9.4", "v0.9.4rc1", "v0.9.4/extra"])
def test_tag_mismatch_rejected(tag):
    with pytest.raises(ValueError, match="does not match"):
        require_tag("0.9.4", tag)


def test_fixture_cannot_overwrite_source(tmp_path):
    with pytest.raises(ValueError, match="destination"):
        materialize(tmp_path, tmp_path, "fixed")

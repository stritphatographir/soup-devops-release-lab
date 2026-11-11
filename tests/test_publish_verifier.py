"""The publisher's inline gate: extracted from release.yml, executed, judged against bundle.py."""

import ast
import os
import subprocess
import sys
from pathlib import Path

import pytest
from bundle import PROJECT, REQUIRES_DIST, REQUIRES_PYTHON
from release_fixture import SHA, TAG, build_bundle, metadata_text
from workflow_source import RELEASE, inline_python, job_text

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
VERIFIER = inline_python()

CASES = [
    pytest.param({}, SHA, TAG, True, "Exact tested release bundle verified.", id="valid"),
    pytest.param({}, "b" * 40, TAG, False, "artifact source SHA mismatch", id="wrong-sha"),
    pytest.param({}, SHA, "v0.9.3", False, "does not match artifact version", id="wrong-tag"),
    pytest.param({}, SHA, "v1", False, "not a vMAJOR.MINOR.PATCH release tag", id="malformed-tag"),
    pytest.param({"wheel_meta": metadata_text(version="9.9.9")}, SHA, TAG, False,
                 "artifact metadata mismatch", id="metadata-drift-rehashed"),
    pytest.param({"sdist_meta": metadata_text(name="soup-release-lab-amir")}, SHA, TAG, False,
                 "artifact metadata mismatch", id="sdist-name-drift"),
    pytest.param({"wheel_meta": metadata_text(requires_dist=())}, SHA, TAG, False,
                 "Requires-Dist mismatch", id="dropped-dependency"),
    pytest.param({"wheel_meta": metadata_text(
        requires_dist=('tomli==2.2.1; python_version < "3.13"',))}, SHA, TAG, False,
        "Requires-Dist mismatch", id="wrong-marker"),
    pytest.param({"sdist_meta": metadata_text(requires_python=">=3.10")}, SHA, TAG, False,
                 "Requires-Python mismatch", id="open-ended-python"),
    pytest.param({"extra": ("soup_release_lab_amirt-0.9.4-py3-none-win_amd64.whl",)},
                 SHA, TAG, False, "unexpected or missing release file", id="extra-file"),
    pytest.param({"wheel_name": "soup_release_lab_amirt-0.9.5-py3-none-any.whl"}, SHA, TAG, False,
                 "published wheel and sdist", id="filename-identity"),
    pytest.param({"source_sha": "c" * 40}, SHA, TAG, False, "artifact source SHA mismatch",
                 id="bound-to-another-commit"),
]


@pytest.fixture(scope="module")
def gate(tmp_path_factory) -> Path:
    """The exact lines the runner pipes into `python -I -`."""
    script = tmp_path_factory.mktemp("publish-gate") / "publish_gate.py"
    script.write_text(VERIFIER, encoding="utf-8", newline="\n")
    return script


def run_gate(script: Path, parent: Path, sha: str | None, tag: str | None,
             optimize: bool = False) -> subprocess.CompletedProcess:
    """Run the extracted gate the way the publish job does: `python -I -` beside release/."""
    env = dict(os.environ)
    for name, value in (("EXPECTED_SHA", sha), ("EXPECTED_TAG", tag)):
        if value is None:
            env.pop(name, None)
        else:
            env[name] = value
    command = [sys.executable, "-I"] + (["-O"] if optimize else []) + [str(script)]
    return subprocess.run(command, cwd=str(parent), env=env, capture_output=True, text=True)


def run_bundle_cli(bundle: Path, sha: str | None, tag: str | None) -> subprocess.CompletedProcess:
    command = [sys.executable, str(SCRIPTS / "bundle.py"), str(bundle)]
    if sha is not None:
        command += ["--source-sha", sha]
    if tag is not None:
        command += ["--tag", tag]
    return subprocess.run(command, capture_output=True, text=True)


def test_the_gate_is_one_heredoc_in_the_publish_job():
    release = RELEASE.read_text(encoding="utf-8")
    assert release.count("<<'PY'") == 1
    assert "python -I - <<'PY'" in release  # -E and -s: no PYTHONPATH, no site-packages
    assert "raise SystemExit" in VERIFIER
    assert "assert " not in VERIFIER


def test_gate_executes_the_published_bundle(tmp_path, gate):
    workspace = tmp_path / "release"
    build_bundle(workspace)
    result = run_gate(gate, tmp_path, SHA, TAG)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "Exact tested release bundle verified."


@pytest.mark.parametrize("fixture,sha,tag,accepted,signal", CASES)
def test_gate_and_bundle_agree_on_every_case(tmp_path, gate, fixture, sha, tag, accepted, signal):
    root = build_bundle(tmp_path / "release", **fixture)
    gate_run = run_gate(gate, tmp_path, sha, tag)
    bundle_run = run_bundle_cli(root, sha, tag)
    assert (gate_run.returncode == 0) is accepted, gate_run.stderr
    assert (bundle_run.returncode == 0) is accepted, bundle_run.stderr
    assert signal in (gate_run.stdout + gate_run.stderr)
    optimized = run_gate(gate, tmp_path, sha, tag, optimize=True)
    assert (optimized.returncode == 0) is accepted, optimized.stderr


@pytest.mark.parametrize("sha,tag,signal", [
    pytest.param("", TAG, "EXPECTED_SHA is not a 40-character commit SHA", id="empty-sha"),
    pytest.param(None, TAG, "EXPECTED_SHA is not a 40-character commit SHA", id="no-sha"),
    pytest.param(SHA, "", "EXPECTED_TAG is not a vMAJOR.MINOR.PATCH release tag", id="empty-tag"),
    pytest.param(SHA, None, "EXPECTED_TAG is not a vMAJOR.MINOR.PATCH release tag", id="no-tag"),
    pytest.param("", "", "EXPECTED_SHA", id="both-empty"),
])
def test_gate_needs_both_identities_of_a_release(tmp_path, gate, sha, tag, signal):
    """A tag-triggered job cannot reach the publisher without a SHA and a tag."""
    build_bundle(tmp_path / "release")
    for optimize in (False, True):
        result = run_gate(gate, tmp_path, sha, tag, optimize=optimize)
        assert result.returncode != 0
        assert signal in (result.stdout + result.stderr)


def test_tampered_bytes_and_missing_manifest_still_fail(tmp_path, gate):
    root = build_bundle(tmp_path / "release")
    (root / "dist/soup_release_lab_amirt-0.9.4.tar.gz").write_bytes(b"replaced")
    for optimize in (False, True):
        result = run_gate(gate, tmp_path, SHA, TAG, optimize=optimize)
        assert result.returncode != 0 and "artifact checksum mismatch" in (
            result.stdout + result.stderr)
    (root / "manifest.json").unlink()
    missing = run_gate(gate, tmp_path, SHA, TAG)
    assert missing.returncode != 0 and "manifest.json is unreadable" in (
        missing.stdout + missing.stderr)


def gate_constants() -> dict[str, object]:
    """The literals the gate pins for itself, read straight out of release.yml."""
    values: dict[str, object] = {}
    for node in ast.parse(VERIFIER).body:
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
            try:
                values[node.targets[0].id] = ast.literal_eval(node.value)
            except (TypeError, ValueError):  # a derived value, e.g. PROJECT.replace(...)
                continue
    return values


def test_inline_gate_and_bundle_pin_the_same_policy():
    constants = gate_constants()
    assert constants["PROJECT"] == PROJECT
    assert constants["REQUIRES_PYTHON"] == REQUIRES_PYTHON
    assert constants["REQUIRES_DIST"] == REQUIRES_DIST


def test_gate_trusts_no_assert_and_no_code_from_the_artifact():
    tree = ast.parse(VERIFIER)
    assert not [node for node in ast.walk(tree) if isinstance(node, ast.Assert)]
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported |= {alias.name.split(".")[0] for alias in node.names}
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                raise AssertionError("the gate must not import code that came with the artifact")
            imported.add((node.module or "").split(".")[0])
    assert imported <= set(sys.stdlib_module_names), imported


def test_privileged_job_runs_nothing_but_the_gate_and_the_publisher():
    publish = job_text("publish")
    assert "id-token: write" in publish
    assert "actions/download-artifact" in publish
    assert "packages-dir: release/dist/" in publish
    for forbidden in ("actions/checkout", "setup-python", "pip install", "build_release",
                      "inject_bug", "smoke_artifact", "matrix_plan", "actions/upload-artifact"):
        assert forbidden not in publish, forbidden

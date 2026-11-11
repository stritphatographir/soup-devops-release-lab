"""Guards on release identity: tags, source SHAs, and the dependency contract."""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from build_release import parse_args as build_args
from bundle import (
    PROJECT,
    REQUIRES_DIST,
    REQUIRES_PYTHON,
    VERSION_SHAPE,
    normalize,
    parse_args,
    require_tag,
    specifiers,
    verify_manifest,
    write_manifest,
)
from inject_bug import materialize
from release_fixture import SHA, TAG, build_bundle, metadata_text
from workflow_source import CHECKS, RELEASE, run_block

ROOT = Path(__file__).resolve().parents[1]
BUILD_CLI = ROOT / "scripts" / "build_release.py"
BUNDLE_CLI = ROOT / "scripts" / "bundle.py"
WHEEL = "dist/soup_release_lab_amirt-0.9.4-py3-none-any.whl"


def make_bundle(tmp_path: Path) -> Path:
    return build_bundle(tmp_path)


def test_bundle_identity(tmp_path):
    root = make_bundle(tmp_path)
    assert verify_manifest(root, SHA, TAG)["version"] == "0.9.4"


def test_stale_artifact_rejected(tmp_path):
    root = make_bundle(tmp_path)
    with pytest.raises(ValueError, match="source SHA"):
        verify_manifest(root, "b" * 40)


def test_tampered_bytes_rejected(tmp_path):
    root = make_bundle(tmp_path)
    (root / WHEEL).write_bytes(b"different bytes")
    with pytest.raises(ValueError, match="checksum"):
        verify_manifest(root)


def test_unexpected_file_rejected(tmp_path):
    root = build_bundle(tmp_path, extra=("soup_release_lab_amirt-0.9.4-py3-none-win_amd64.whl",))
    with pytest.raises(ValueError, match="unexpected"):
        verify_manifest(root)


def test_manifest_path_traversal_rejected(tmp_path):
    root = make_bundle(tmp_path)
    manifest_path = root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["files"]["../outside.whl"] = manifest["files"].pop(
        "soup_release_lab_amirt-0.9.4-py3-none-any.whl")
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError):
        verify_manifest(root)


@pytest.mark.parametrize("tag", ["v0.9.3", "0.9.4", "v0.9.4rc1", "v0.9.4/extra"])
def test_tag_mismatch_rejected(tag):
    with pytest.raises(ValueError, match="does not match"):
        require_tag("0.9.4", tag)


def test_fixture_cannot_overwrite_source(tmp_path):
    with pytest.raises(ValueError, match="destination"):
        materialize(tmp_path, tmp_path, "fixed")


# --- F2: an absent optional tag is not the same thing as a tag with no value ---


def test_omitted_tag_is_a_non_release_check(tmp_path):
    root = make_bundle(tmp_path)
    assert verify_manifest(root, SHA)["version"] == "0.9.4"
    assert verify_manifest(root, SHA, None)["source_sha"] == SHA


def test_empty_tag_is_rejected(tmp_path):
    root = make_bundle(tmp_path)
    with pytest.raises(ValueError, match="tag was supplied empty"):
        verify_manifest(root, SHA, "")
    with pytest.raises(ValueError, match="tag was supplied empty"):
        require_tag("0.9.4", "")


def test_empty_source_sha_is_rejected(tmp_path):
    root = make_bundle(tmp_path)
    with pytest.raises(ValueError, match="source SHA was supplied empty"):
        verify_manifest(root, "")
    with pytest.raises(ValueError, match="source SHA was supplied empty"):
        write_manifest(tmp_path / "nowhere", "0.9.4", "")


@pytest.mark.parametrize("sha,tag,succeeds", [
    pytest.param(SHA, TAG, True, id="exact"),
    pytest.param("b" * 40, TAG, False, id="wrong-sha"),
    pytest.param(SHA, "v0.9.3", False, id="wrong-tag"),
    pytest.param(SHA, None, True, id="branch-run"),
    pytest.param(SHA, "", False, id="empty-tag"),
    pytest.param("", TAG, False, id="empty-sha"),
    pytest.param(None, None, True, id="local-read-back"),
])
def test_release_gates_on_supplied_identity(tmp_path, sha, tag, succeeds):
    root = make_bundle(tmp_path)
    if succeeds:
        assert verify_manifest(root, sha, tag)["version"] == "0.9.4"
    else:
        with pytest.raises(ValueError):
            verify_manifest(root, sha, tag)


def test_cli_rejects_supplied_empty_values(tmp_path, capsys):
    make_bundle(tmp_path)
    for flag, message in [("--tag", "--tag needs a release tag"),
                          ("--source-sha", "--source-sha needs a commit")]:
        with pytest.raises(SystemExit) as exit_code:
            parse_args([str(tmp_path), flag, ""])
        assert exit_code.value.code == 2
        assert message in capsys.readouterr().err
    assert parse_args([str(tmp_path)]).tag is None
    assert parse_args([str(tmp_path), "--source-sha", SHA]).source_sha == SHA


def test_cli_keeps_local_and_docker_calls_working(tmp_path):
    """`bundle.py <dir> --source-sha <sha>` is the call the Dockerfile makes."""
    make_bundle(tmp_path)
    ok = subprocess.run([sys.executable, str(BUNDLE_CLI), str(tmp_path), "--source-sha", SHA],
                        capture_output=True, text=True)
    assert ok.returncode == 0, ok.stderr
    assert json.loads(ok.stdout)["source_sha"] == SHA
    empty = subprocess.run(
        [sys.executable, str(BUNDLE_CLI), str(tmp_path), "--source-sha", SHA, "--tag", ""],
        capture_output=True, text=True)
    assert empty.returncode == 2 and "omit it outside a release" in empty.stderr


def test_build_release_cli_tag_is_optional_never_empty(tmp_path, monkeypatch):
    monkeypatch.delenv("GITHUB_SHA", raising=False)
    assert build_args(["--out", str(tmp_path / "x")]).tag is None
    assert build_args(["--out", str(tmp_path / "x"), "--tag", TAG]).tag == TAG
    assert build_args(["--out", str(tmp_path / "x")]).source_sha == "local-uncommitted"
    monkeypatch.setenv("GITHUB_SHA", SHA)
    assert build_args(["--out", str(tmp_path / "x")]).source_sha == SHA
    with pytest.raises(SystemExit) as exit_code:
        build_args(["--out", str(tmp_path / "x"), "--tag", ""])
    assert exit_code.value.code == 2


# --- F9: the published dependency contract, not the consumer venv, is the evidence ---


@pytest.mark.parametrize("drift,expected", [
    pytest.param({"requires_dist": ()}, "Requires-Dist mismatch", id="dropped-dependency"),
    pytest.param({"requires_dist": ('tomli==2.2.1; python_version < "3.13"',)},
                 "Requires-Dist mismatch", id="wrong-marker"),
    pytest.param({"requires_dist": ("tomli==2.2.1",)},
                 "Requires-Dist mismatch", id="unmarked-dependency"),
    pytest.param({"requires_dist": ('tomllib==2.2.1; python_version < "3.11"',)},
                 "Requires-Dist mismatch", id="swapped-dependency"),
    pytest.param({"requires_dist": ('tomli==2.3.0; python_version < "3.11"',)},
                 "Requires-Dist mismatch", id="moved-off-the-lock"),
    pytest.param({"requires_python": None}, "Requires-Python mismatch", id="no-python-floor"),
    pytest.param({"requires_python": ">=3.10"}, "Requires-Python mismatch", id="open-ended-python"),
    pytest.param({"requires_python": ">=3.11,<3.15"}, "Requires-Python mismatch", id="wrong-floor"),
    pytest.param({"name": "soup-release-lab-amir"}, "metadata mismatch", id="wrong-name"),
    pytest.param({"version": "0.9.3"}, "metadata mismatch", id="wrong-version"),
])
def test_declared_dependency_drift_is_rejected(tmp_path, drift, expected):
    root = build_bundle(tmp_path, wheel_meta=metadata_text(**drift))
    with pytest.raises(ValueError, match=expected):
        verify_manifest(root, SHA, TAG)


def test_sdist_dependency_drift_is_rejected(tmp_path):
    root = build_bundle(tmp_path, sdist_meta=metadata_text(requires_dist=()))
    with pytest.raises(ValueError, match="Requires-Dist mismatch"):
        verify_manifest(root, SHA, TAG)


def test_build_time_manifest_refuses_dependency_drift(tmp_path):
    """The gate fires while building, so an undeclared dependency is never published."""
    root = build_bundle(tmp_path, wheel_meta=metadata_text(requires_dist=()))
    with pytest.raises(ValueError, match="Requires-Dist mismatch"):
        write_manifest(root, "0.9.4", SHA, TAG)


def test_distribution_filename_is_bound_to_the_identity(tmp_path):
    root = build_bundle(tmp_path, wheel_name="soup_release_lab_amirt-0.9.4-py3-none-win_amd64.whl")
    with pytest.raises(ValueError, match="published wheel and sdist"):
        verify_manifest(root, SHA, TAG)


def test_dependency_policy_is_the_project_own_contract():
    """The pinned metadata policy has to keep following pyproject.toml."""
    try:
        import tomllib
    except ModuleNotFoundError:  # Python 3.10 is part of the supported contract.
        import tomli as tomllib
    with (ROOT / "pyproject.toml").open("rb") as stream:
        project = tomllib.load(stream)["project"]
    assert PROJECT == project["name"]
    assert [normalize(item) for item in project["dependencies"]] == list(REQUIRES_DIST)
    assert specifiers(project["requires-python"]) == specifiers(REQUIRES_PYTHON)
    assert VERSION_SHAPE.fullmatch(project["version"])


# --- F2 in the runner: the workflow must not hand an empty value to --tag ---

RECORD = (
    'python() {\n'
    '  printf "ARGS"\n'
    '  for a in "$@"; do printf " [%s]" "$a"; done\n'
    '  printf "\\n"\n'
    '}\n'
)


def usable_bash() -> str | None:
    """First shell that really runs; Windows ships a WSL bash.exe that cannot start."""
    candidates = (os.environ.get("RELEASE_TEST_BASH"), shutil.which("bash"), "/bin/bash",
                  r"C:\Program Files\Git\bin\bash.exe", r"C:\Program Files\Git\usr\bin\bash.exe")
    for candidate in candidates:
        if not candidate or not Path(candidate).is_file():
            continue
        try:
            probe = subprocess.run([candidate, "-c", "printf bash-ok"],
                                   capture_output=True, text=True, timeout=30)
        except (OSError, subprocess.TimeoutExpired):
            continue
        if probe.returncode == 0 and "bash-ok" in probe.stdout:
            return candidate
    return None


BASH = usable_bash()


@pytest.mark.skipif(BASH is None, reason="no usable bash on this host")
@pytest.mark.parametrize("step", ["Build once and bind identities",
                                  "Verify source, tag, and distribution hashes"])
@pytest.mark.parametrize("ref_type,ref_name,release_tag,succeeds,carries_tag", [
    pytest.param("tag", "v0.9.4", "v0.9.4", True, True, id="release-leg"),
    pytest.param("branch", "main", "", True, False, id="branch-leg"),
    pytest.param("pull_request", "12", "", True, False, id="pull-request-leg"),
    pytest.param("tag", "v0.9.4", "", False, False, id="tag-leg-loses-the-input"),
    pytest.param("tag", "v0.9.4", "v0.9.3", False, False, id="tag-leg-disagrees-with-the-ref"),
    pytest.param("branch", "main", "v0.9.4", False, False, id="branch-leg-invents-a-tag"),
])
def test_workflow_tag_argument_fails_closed(tmp_path, step, ref_type, ref_name, release_tag,
                                            succeeds, carries_tag):
    script = tmp_path / "step.sh"
    script.write_text(RECORD + run_block(step, CHECKS), encoding="utf-8", newline="\n")
    env = {**os.environ, "GITHUB_REF_TYPE": ref_type, "GITHUB_REF_NAME": ref_name,
           "RELEASE_TAG": release_tag, "RUNNER_TEMP": str(tmp_path), "GITHUB_SHA": SHA}
    assert BASH is not None  # guaranteed by skipif; stated so the type checker agrees
    result = subprocess.run([BASH, "-e", str(script)], capture_output=True, text=True, env=env)
    assert (result.returncode == 0) is succeeds, result.stdout + result.stderr
    invocations = [line for line in result.stdout.splitlines() if line.startswith("ARGS")]
    assert bool(invocations) is succeeds
    if succeeds:
        tokens = [token.strip("[]") for token in invocations[0].split()[1:]]
        assert ("--tag" in tokens) is carries_tag
        if carries_tag:
            assert tokens[tokens.index("--tag") + 1] == TAG
    else:
        assert "::error::" in result.stdout


def test_release_workflow_still_forwards_its_own_tag():
    assert "release-tag: ${{ github.ref_name }}" in RELEASE.read_text(encoding="utf-8")
    assert "release-tag:\n        type: string\n        default: ''" in CHECKS.read_text(
        encoding="utf-8")
    assert "release-tag" not in (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")

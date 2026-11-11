"""Read the shell and YAML that really live in the workflow files, without a YAML parser."""

from pathlib import Path

WORKFLOWS = Path(__file__).resolve().parents[1] / ".github" / "workflows"
RELEASE = WORKFLOWS / "release.yml"
CHECKS = WORKFLOWS / "checks.yml"


def _lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


def _dedent(body: list[str], where: str) -> str:
    if not any(line.strip() for line in body):
        raise AssertionError(f"empty block for {where}")
    width = min(len(line) - len(line.lstrip()) for line in body if line.strip())
    return "\n".join(line[width:] if line.strip() else "" for line in body) + "\n"


def inline_python(path: Path = RELEASE, marker: str = "<<'PY'") -> str:
    """The quoted-heredoc body exactly as the runner hands it to `python -I -`."""
    lines = _lines(path)
    try:
        start = next(i for i, line in enumerate(lines) if line.rstrip().endswith(marker))
    except StopIteration:  # noqa: PERF203 - short list, clearer than a flag
        raise AssertionError(f"no {marker} heredoc in {path.name}") from None
    body = []
    for line in lines[start + 1:]:
        if line.strip() == "PY":
            return _dedent(body, f"{path.name} heredoc")
        body.append(line)
    raise AssertionError(f"unterminated heredoc in {path.name}")


def run_block(step_name: str, path: Path = CHECKS) -> str:
    """The literal `run: |` block of one step, dedented as Actions would feed bash."""
    lines = _lines(path)
    header = f"name: {step_name}"
    try:
        start = next(i for i, line in enumerate(lines)
                     if line.strip() in (header, f"- {header}"))
    except StopIteration:
        raise AssertionError(f"no step named {step_name!r} in {path.name}") from None
    try:
        block = next(i for i, line in enumerate(lines[start + 1:], start + 1)
                     if line.strip().startswith("run: |"))
    except StopIteration:
        raise AssertionError(f"step {step_name!r} has no run block in {path.name}") from None
    indent = len(lines[block]) - len(lines[block].lstrip())
    body = []
    for line in lines[block + 1:]:
        if line.strip() and len(line) - len(line.lstrip()) <= indent:
            break
        body.append(line)
    return _dedent(body, f"{path.name}:{step_name}")


def job_text(job: str, path: Path = RELEASE) -> str:
    """The body of one job, so privilege and step-shape can be asserted on real text."""
    lines = _lines(path)
    try:
        start = next(i for i, line in enumerate(lines)
                     if line.strip() == f"{job}:" and len(line) - len(line.lstrip()) == 2)
    except StopIteration:
        raise AssertionError(f"no {job} job in {path.name}") from None
    body = []
    for line in lines[start + 1:]:
        if line.strip() and len(line) - len(line.lstrip()) <= 2:
            break
        body.append(line)
    return "\n".join(body) + "\n"

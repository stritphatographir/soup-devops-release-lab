# Soup DevOps take-home

My submission for the Soup DevOps internship. It explores one question: **when
is a green pipeline enough to trust a Python release?**

The project is a small CLI, `soup-check`, that reads a TOML service config and
prints a JSON report. Four isolated fixtures recreate a broken **0.9.3**;
**0.9.4** is the fixed release.

## Four bugs that naive CI misses

| Bug | Why users hit it |
| --- | --- |
| Python compatibility | An unconditional `tomllib` import breaks Python 3.10. |
| Windows startup | A Unix-only `pwd` import prevents the CLI from starting. |
| Missing package data | The installed wheel is missing `defaults.json`. |
| Broken entry point | The console command points to a function that does not exist. |

All four pass the naive Linux checks and build successfully. The hardened
pipeline rejects each one in an installed consumer.
[Red/green runs and original logs](evidence/README.md) are retained, including
earlier infrastructure failures.

## Pipeline and results

- Lint, types, dependency audit, and **107 passing tests**.
- One build, then clean wheel/sdist consumers across **Python 3.10-3.14 on
  Linux, Windows, and macOS**, plus Docker.
- Tag-triggered TestPyPI publishing through **OIDC**, using the exact tested
  artifact, followed by public download, hash checks, and installation tests.

[CI: 19/19 passed](https://github.com/stritphatographir/soup-devops-release-lab/actions/runs/43226717548)
| [Release: 21/21 passed](https://github.com/stritphatographir/soup-devops-release-lab/actions/runs/43224278803)
| [TestPyPI 0.9.4](https://test.pypi.org/project/soup-release-lab-amirt/0.9.4/)

## Reproduce locally

The full reproduction needs **Windows, Python 3.10+, and Docker running Linux
containers**. Run from the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip --isolated install --index-url https://pypi.org/simple --no-cache-dir --only-binary=:all: --require-hashes -r requirements/ci.lock
.\.venv\Scripts\python.exe scripts/reproduce.py --out evidence/local/my-reproduction
```

Use a new output directory each time. The script checks all four intended
failures and six fixed wheel/sdist consumers without changing the source.

## Verdict and submission

**Automate TestPyPI; keep human approval for real PyPI.** Hashes and passing
tests cannot establish that a compromised maintainer or runner is trustworthy.
Independent review, protected release changes, recovery controls, and a durable
release circuit breaker remain priorities.

- [Two-page note](output/pdf/Soup-DevOps-Release-Note.pdf)
- [Supply-chain controls and limitations](docs/SECURITY.md)
- [GPU design and budget](docs/GPU_CI.md) - design only; no GPU was rented.
- [Publishing procedure](docs/PUBLISHING.md)
- [Reflection draft](docs/REFLECTION.md)

I used Codex for implementation and automated checks, and requested OpenCode
and Antigravity as additional reviewers. I handled account login and verification,
requested a hook retry, and flagged the GitHub identity issue. The
[AI-use disclosure](docs/AI_USAGE.md) separates my involvement from tool-run
verification and links the supporting evidence.

The immutable TestPyPI description comes from the tagged README and predates
the publication-status update; the current results are linked above.

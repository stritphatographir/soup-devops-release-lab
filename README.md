# Soup DevOps take-home

My submission for the Soup DevOps internship. It explores one question: **when
is a green pipeline enough to trust a Python release?**

**Short answer:** enough for TestPyPI, not yet for real PyPI without a human.
The pipeline caught all four bugs that naive CI let through, and published
0.9.4 to TestPyPI over OIDC without a long-lived PyPI token. It cannot yet tell whether a
compromised maintainer or runner should be trusted. See the
[verdict](#verdict-and-submission).

The project is a small CLI, `soup-check`, that reads a TOML service config and
prints a JSON report. Four isolated fixtures recreate a broken **0.9.3**;
**0.9.4** is the fixed release.

## Four bugs that naive CI misses

| Bug | Why users hit it | Naive CI | Hardened CI |
| --- | --- | --- | --- |
| Python compatibility | An unconditional `tomllib` import breaks Python 3.10. | [Passed](https://github.com/stritphatographir/soup-devops-release-lab/actions/runs/43100255326) | [Failed](https://github.com/stritphatographir/soup-devops-release-lab/actions/runs/43100260410) |
| Windows startup | A Unix-only `pwd` import prevents the CLI from starting. | [Passed](https://github.com/stritphatographir/soup-devops-release-lab/actions/runs/43100265599) | [Failed](https://github.com/stritphatographir/soup-devops-release-lab/actions/runs/43100269894) |
| Missing package data | The installed wheel is missing `defaults.json`. | [Passed](https://github.com/stritphatographir/soup-devops-release-lab/actions/runs/43100274474) | [Failed](https://github.com/stritphatographir/soup-devops-release-lab/actions/runs/43100278631) |
| Broken entry point | The console command points to a function that does not exist. | [Passed](https://github.com/stritphatographir/soup-devops-release-lab/actions/runs/43100283422) | [Failed](https://github.com/stritphatographir/soup-devops-release-lab/actions/runs/43100288844) |

The table links to GitHub Actions runs. All four pass naive Linux checks and build successfully. The hardened pipeline rejects each in an installed consumer. The note also cites a separate local reproduction.
[Red/green runs and original logs](evidence/README.md) are retained, including
earlier infrastructure failures.

## Pipeline and results

- Lint, types, dependency audit, and **107 passing tests with 96.15% combined package line/branch coverage**.
- One build, then clean wheel/sdist consumers across **Python 3.10-3.14 on
  Linux, Windows, and macOS**, plus Docker.
- Tag-triggered TestPyPI publishing through **OIDC**, using the exact tested
  artifact, followed by public download, hash checks, and installation tests.

[CI: 19/19 passed](https://github.com/stritphatographir/soup-devops-release-lab/actions/runs/43226717548)
| [Release: 21/21 passed](https://github.com/stritphatographir/soup-devops-release-lab/actions/runs/43224278803)
| [TestPyPI 0.9.4](https://test.pypi.org/project/soup-release-lab-amirt/0.9.4/)


TestPyPI displays the README from the release tag, which predates the publication update.

## Reproduce locally

The full reproduction needs **Windows, Python 3.10-3.14, and Docker running Linux
containers**. Run from the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip --isolated install --index-url https://pypi.org/simple --no-cache-dir --only-binary=:all: --require-hashes -r requirements/ci.lock
.\.venv\Scripts\python.exe scripts/reproduce.py --out evidence/local/my-reproduction
```

Use a new output directory each time. The script checks all four intended
failures and six fixed wheel/sdist consumers without changing the source.

## What this does not catch

- A compromised maintainer or runner can control both the build and its evidence.
- Hash checks preserve the chosen bytes, including malicious ones.
- The matrix leaves some architectures and user environments untested. Downstream users do not automatically inherit our hash lock.
- GPU paths are outside the executed checks.

## Silent failures closed

- Unpinned or swapped dependencies. [checks.yml](.github/workflows/checks.yml) and [smoke_artifact.py](scripts/smoke_artifact.py) install from one index with hash locks.
- Hidden resolver errors. [smoke_artifact.py](scripts/smoke_artifact.py) uses fresh consumer environments and disables the pip cache for dependency bootstrap.
- Stale artifacts. [release.yml](.github/workflows/release.yml) downloads the tested artifact by ID and checks its commit and hashes before upload.
- Fork PR access to publishing credentials. [ci.yml](.github/workflows/ci.yml) runs PR checks with read-only permissions. [release.yml](.github/workflows/release.yml) gives OIDC permission to the tag-triggered publisher.
- Tag/version drift. [release.yml](.github/workflows/release.yml) requires the tag to match the distribution version.

Why these: each is a way for a green run to approve something other than what
users receive. If I had to defend three first: (1) publishing the exact tested
artifact, where the artifact ID and hash checks guard against stale or
substituted bytes and a separate explicit tag-to-version check catches version
drift;
(2) hash-locked installs from a single index to constrain dependency versions
and bytes, with fresh environments and `pip check` to expose resolver errors;
(3) OIDC limited to one publisher job
with fork PR jobs running read-only and receiving no publishing credentials.
Malicious dependencies chosen during lock updates and resolution in downstream
environments remain open.

## Verdict and submission

**Can it publish to real PyPI with no human? Not yet.** TestPyPI can be automated. First, require independent review and protection for source, workflow, lockfile, and release-tag changes, and verify account recovery.

- [Two-page note](output/pdf/Soup-DevOps-Release-Note.pdf)
- [Supply-chain controls and limitations](docs/SECURITY.md)
- [GPU design and budget](docs/GPU_CI.md) - design only, estimated at $8.76/month. No GPU was rented.
- [Publishing procedure](docs/PUBLISHING.md)
- [Reflection](docs/REFLECTION.md)

## How I used AI

I ran this as a multi-agent job in **Orca**, an app that runs several coding
agents side by side. **Codex** built it; **OpenCode** and **Antigravity**
reviewed it. Nearly all code, workflows and tests were written by these tools,
not by me. Full detail: [AI-use disclosure](docs/AI_USAGE.md).

| Tool | Used for | What I accepted | Where it fell short |
| --- | --- | --- | --- |
| Codex | CLI, four fault fixtures, workflows, tests, local checks, TestPyPI publisher setup | Most of the build | Its first pins (pytest, setuptools, wheel) **failed the dependency audit**. It repinned, relocked and reran; the [failed audit](evidence/local/initial-dependency-audit.txt) is kept. |
| OpenCode | Pipeline review, then verifier fixes | Tag identity, dependency metadata and explicit-failure checks. OpenCode identified the Docker artifact issue; Codex implemented that fix. | A concern about artifact-download permissions **did not reproduce** in hosted runs, so it was not acted on. |
| Antigravity | Review of evidence, GPU cost, cleanup, release controls | All six findings were addressed | Its follow-up stalled and a retry hit a provider quota error. I did not switch models; Codex applied the documented fixes. |

**What I did myself:** logged into and verified the GitHub and TestPyPI
accounts (Codex then configured the TestPyPI publisher), requested the two
reviews, and flagged that commits were attributed to the wrong GitHub account.
Codex corrected the commit identity and checked the next commit's author,
committer, and push actor through GitHub's API.

**What I have not done:** reviewed the code or Actions logs, or re-run the checks by hand.
Everything marked "verified" here was run by a tool or by GitHub Actions. You
can check the core claim in minutes without trusting that:

1. Open a naive run and its hardened twin from the [table above](#four-bugs-that-naive-ci-misses). The first is green, the second red.
2. Read the failing consumer log for the named error, such as `pwd`.
3. Or run `scripts/reproduce.py` as shown under [Reproduce locally](#reproduce-locally).

Review records: [resolution ledger](docs/reviews/RESOLUTIONS.md).

# Soup release pipeline lab

A Python CLI and a release pipeline that demonstrate why green source tests do
not prove that the distribution a user installs will work. The fixed version is
**0.9.4**. Four isolated fixtures reconstruct a broken **0.9.3** release.

```console
python -m pip install --require-hashes -r requirements/ci.lock
python scripts/build_release.py --out tmp/release
python scripts/smoke_artifact.py --bundle tmp/release --kind wheel
python scripts/smoke_artifact.py --bundle tmp/release --kind sdist
```

The CLI command is `soup-check inspect examples/service.toml`. Python 3.10 through
3.14 on Linux, Windows, and macOS are the configured support contract in Actions.

## Current evidence

Four local fixtures passed the naive library tests and build, then each failed
in a clean installed consumer for its intended reason. Fixed wheel and sdist
consumers passed on Linux Python 3.10/3.12 and native Windows Python 3.13.
The recorded unit suite passed with 96.15% combined line/branch coverage.
Lint, type checks, workflow lint, and the updated dependency audit passed.
The unprivileged Docker runtime also launched successfully.

**Hosted red/green evidence is verified.** All four naive
experiments passed; all four hardened runs failed at the required consumer with
the intended signature. The fixed run passed all 19 jobs, including the 15-leg
OS/Python matrix and the Docker check of the exact same artifact.
The stronger verifier at `feb2268` then passed another full fixed run and four
fresh fault regressions, all with source-quality green.
Initial Actions dispatches returned
GitHub internal startup failures before creating any jobs. These are retained
as infrastructure failures, not counted as package-bug detections. Further
diagnostic/retry runs and actual statuses are in the [evidence ledger](evidence/README.md).
**TestPyPI publication and public read-back passed.** The
[v0.9.4 release run](https://github.com/stritphatographir/soup-devops-release-lab/actions/runs/43224278803)
passed all 21 jobs: the 19 checks, OIDC publication, and public wheel/sdist
read-back on Python 3.10. The [published package](https://test.pypi.org/project/soup-release-lab-amirt/0.9.4/)
has exactly the tested file hashes. A fresh Windows Python 3.13 consumer also
downloaded the wheel from the public Simple Index, checked its hash, and passed.
Public provenance identity and digest fields were inspected; independent
cryptographic signature verification was not performed.

## Read the submission

- [Two-page note (PDF)](output/pdf/Soup-DevOps-Release-Note.pdf) and [editable source](docs/NOTE.md)
- [Actual logs and Actions links](evidence/README.md)
- [Supply-chain controls and trust boundaries](docs/SECURITY.md)
- [GPU design and monthly budget](docs/GPU_CI.md)
- [OIDC setup and remote reproduction commands](docs/PUBLISHING.md)
- [AI disclosure](docs/AI_USAGE.md) and [reflection draft](docs/REFLECTION.md)
- [Independent review records](docs/reviews/)

## Reproduce all four incidents locally

The full reproduction driver requires Windows, Python, and a running Linux
Docker engine. It uses digest-pinned Linux 3.10/3.12 tool images and native
Windows for the Unix-import fault. Every raw command and exit code is retained.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip --isolated install --index-url https://pypi.org/simple --no-cache-dir --only-binary=:all: --require-hashes -r requirements/ci.lock
.\.venv\Scripts\python.exe scripts/reproduce.py --out evidence/local/my-reproduction
```

Use a new output directory for each run to keep earlier failures. Each fixture
lives in `tmp/`; the checkout is never mutated. The driver exits successfully
only when the naive tests/build pass, the faulty consumer fails with the exact
expected signature, and all six fixed consumers pass. This local harness is
distinct from Actions, where faulty runs must really be red.

For individual examples:

```console
python scripts/inject_bug.py --bug missing-data --destination tmp/missing-data
python scripts/naive_check.py --source tmp/missing-data
python scripts/build_release.py --source tmp/missing-data --out tmp/broken-release
python scripts/smoke_artifact.py --bundle tmp/broken-release --kind wheel
```

The last command deliberately fails. Other choices are `python310`, `windows`,
`entrypoint`, and `fixed`; see the evidence ledger for the required environment.

## Release flow

`naive.yml` demonstrates source-only checks. `ci.yml` calls `checks.yml` for
quality, one sdist-to-wheel build, a clean consumer matrix, and Docker. Fixed
runs use 15 OS/Python combinations; fault experiments use three representative
ones. The existing `v0.9.4` tag invoked the same checks in `release.yml`; only after all
pass can the OIDC job upload the exact tested artifact to TestPyPI. Its public
bytes are downloaded and exercised again. There is no real-PyPI publisher.

The immutable TestPyPI 0.9.4 description is the README from the tagged commit,
so it predates this publication-status update. The current evidence is linked
above and retained in the repository.

Runtime and build dependencies are hash-locked, the normal consumer path uses no
editable install or source import path, and neither a restored venv nor pip
cache is used as proof of installation. A green result still has the limits in
[the threat model](docs/SECURITY.md).

The report PDF can be regenerated with Python 3.10+ after installing
`requirements/docs.lock` using `--require-hashes`, then running
`python scripts/render_note.py`. The note was rendered and checked to be two pages.

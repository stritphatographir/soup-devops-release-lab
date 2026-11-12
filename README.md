# Soup DevOps release lab

A small Python CLI used to answer a release-engineering question: **can a green
source test suite justify publishing the package users will install?**

Four isolated faults pass naive Linux CI and fail in clean installed consumers.
The fixed **0.9.4** release demonstrates:

- **Installed wheel and sdist testing** across 15 native OS/Python combinations,
  plus Docker using the same build artifact.
- **Publication of tested bytes:** artifact ID, source commit, tag/version,
  distribution metadata, and SHA-256 checks before an isolated OIDC publisher.
- **Public read-back:** the TestPyPI wheel and sdist are downloaded, compared
  with the tested manifest, installed, and exercised again.

Recorded results: [fixed CI, 19/19 jobs](https://github.com/stritphatographir/soup-devops-release-lab/actions/runs/43226717548)
| [TestPyPI release, 21/21 jobs](https://github.com/stritphatographir/soup-devops-release-lab/actions/runs/43224278803)
| [published 0.9.4](https://test.pypi.org/project/soup-release-lab-amirt/0.9.4/).
These are historical executions. The [evidence ledger](evidence/README.md)
preserves release and fault-regression logs, source revisions, and earlier failures.

**My involvement:** AI agents generated the implementation. I reviewed the core
parts and remained involved throughout development. Historical package-check
execution belongs to the agents and GitHub Actions. I separately executed an
AI-generated [RTX 5090 lab probe](docs/GPU_LAB_RESULTS.md): 65,536 vector-add
results matched a CPU reference, the no-GPU control failed, and a CPU-only
timeout control returned 124. [The disclosure](docs/AI_USAGE.md) separates these
contributions; this lab is not a GPU release-pipeline run.

## What the application does

`soup-check inspect <config.toml>` reads a `[service]` table and packaged JSON
defaults, validates the name and worker count, and prints a JSON report.
Workers must be integers from 1 to 16 and default to 1; the service name must
be non-empty. Invalid configuration or an unreadable file returns exit code 2.

For [examples/service.toml](examples/service.toml), the result is:

```json
{"name": "example service", "profile": "safe", "schema": 1, "workers": 3}
```

## Architecture and release flow

| Component | Responsibility |
| --- | --- |
| [CLI and core](src/soup_release_lab/cli.py), [validation](src/soup_release_lab/core.py), [defaults](src/soup_release_lab/data/defaults.json) | TOML input, validation, packaged resources, JSON output |
| [Fault injector](scripts/inject_bug.py) and [naive checks](scripts/naive_check.py) | Copy isolated candidates and demonstrate what editable library tests miss |
| [Build](scripts/build_release.py) and [bundle verifier](scripts/bundle.py) | Build sdist then wheel; bind filenames, metadata, source identity, and hashes |
| [Consumer harness](scripts/smoke_artifact.py), [matrix planner](scripts/matrix_plan.py), [Dockerfile](Dockerfile) | Exercise installed distributions outside the source checkout |
| [Release workflow](.github/workflows/release.yml) and [read-back](scripts/read_back.py) | Verify and publish the same bundle, then check the public bytes |

1. [Reusable checks](.github/workflows/checks.yml) run lint, types, dependency
   audit, unit tests, and one build. The fixed matrix covers Python **3.10-3.14**
   on Linux, Windows, and macOS.
2. Fresh wheel and sdist consumers run outside the checkout, checking imports,
   both entry points, versions, valid/invalid input, and Unicode paths.
3. The tag-triggered publisher waits for every check and verifies the same-run
   artifact ID, source SHA, tag/version, metadata, and hashes. Only this job
   gets `id-token: write`; it has no checkout, dependency install, or rebuild.
4. Public read-back downloads and installs both distributions. It detects
   changed public bytes after publication and cannot undo the upload.

Dependencies use exact hash locks and one canonical bootstrap index. Candidate
installs disable dependency resolution and index access with `--no-deps --no-index`;
metadata checks prevent that setup from hiding a missing declared dependency. Fork PR checks are read-only and
receive no publishing credentials. See [the threat model](docs/SECURITY.md)
for boundaries and [publishing details](docs/PUBLISHING.md) for the OIDC mapping.

## Four bugs that naive CI misses

Every pair uses the same source revision: naive builds pass; hardened runs
fail in the intended consumer with source-quality checks green.

| Fault | Rejecting consumer | Naive | Hardened |
| --- | --- | --- | --- |
| Unconditional `tomllib` import | Linux Python 3.10 CLI | [green](https://github.com/stritphatographir/soup-devops-release-lab/actions/runs/43100255326) | [red](https://github.com/stritphatographir/soup-devops-release-lab/actions/runs/43100260410) |
| Unix-only `pwd` import | Native Windows CLI | [green](https://github.com/stritphatographir/soup-devops-release-lab/actions/runs/43100265599) | [red](https://github.com/stritphatographir/soup-devops-release-lab/actions/runs/43100269894) |
| Missing `defaults.json` | Installed wheel resource read | [green](https://github.com/stritphatographir/soup-devops-release-lab/actions/runs/43100274474) | [red](https://github.com/stritphatographir/soup-devops-release-lab/actions/runs/43100278631) |
| Invalid console entry point | Installed `soup-check` executable | [green](https://github.com/stritphatographir/soup-devops-release-lab/actions/runs/43100283422) | [red](https://github.com/stritphatographir/soup-devops-release-lab/actions/runs/43100288844) |

[Collected logs](evidence/README.md#verified-hosted-red-and-green-evidence)
match each failure to its intended consumer and error. Broken fixtures are
version 0.9.3 and are never published.

## Build and try the CLI

Use Python 3.10-3.14 from the repository root. PowerShell example:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip --isolated install --index-url https://pypi.org/simple --no-cache-dir --only-binary=:all: --require-hashes -r requirements/ci.lock
.\.venv\Scripts\python.exe scripts/build_release.py --out tmp/quickstart-release
.\.venv\Scripts\python.exe -m pip --isolated install --no-deps --no-index tmp/quickstart-release/dist/soup_release_lab_amirt-0.9.4-py3-none-any.whl
.\.venv\Scripts\soup-check.exe inspect examples/service.toml
```

On Linux/macOS, use `.venv/bin/python` and `.venv/bin/soup-check` instead of
the Windows executable paths. Building requires a **new output directory**;
choose another path on a later attempt. Bootstrap dependencies need internet
access. The local build is labelled `local-uncommitted`, not a release.

Check the actual distributions and run unit tests:

```powershell
.\.venv\Scripts\python.exe scripts/smoke_artifact.py --bundle tmp/quickstart-release --kind wheel
.\.venv\Scripts\python.exe scripts/smoke_artifact.py --bundle tmp/quickstart-release --kind sdist
.\.venv\Scripts\python.exe -m pytest --cov --cov-branch --cov-report=term-missing
```

## Reproduce locally

The complete four-fault reproduction requires **native Windows, a supported
host Python, and Docker running Linux containers**. It supplies Linux Python
3.10/3.12 through containers and uses the host Python for Windows:

```powershell
.\.venv\Scripts\python.exe scripts/reproduce.py --out evidence/local/my-reproduction
```

Use a new evidence directory. The driver expects four naive/build passes,
four intended consumer failures, and six fixed wheel/sdist passes. It does
not reproduce the full hosted matrix locally. See [verification](docs/VERIFICATION.md)
for check scope and [manual check suggestions](docs/PERSONAL_CHECKS.md).

## Limitations and verdict

**Automate TestPyPI; retain human approval before enabling real PyPI.** This
repository has no real-PyPI publisher. Priorities are independent review and
protected source/workflow/lock/tag changes, recovery procedures, and a durable
release circuit breaker; the current breaker is manual.

Hashes can identify malicious bytes too. A compromised maintainer or runner
can control both build and evidence. The matrix does not cover every
architecture, system library, resolver combination, or user environment.
The recorded 96.15% coverage measures the small application package, not the
whole pipeline. Setting a build timestamp does not establish independently
reproducible builds. Public provenance fields/digests were inspected without
independent signature verification.

[GPU CI](docs/GPU_CI.md) remains a design and dated rental-cost estimate.
The separate [manual lab](docs/GPU_LAB_RESULTS.md) checks basic CUDA execution
and container cleanup, not GPU application behavior, automated GPU CI, or
cloud cost controls. The immutable TestPyPI description comes from the release
tag and predates these documentation updates.

## How I used AI

Codex implemented and coordinated checks; OpenCode reviewed and fixed verifiers;
Antigravity reviewed the design, with its failed follow-up recorded. I requested
the additional reviews, handled account access, and flagged commit identity.
[The disclosure](docs/AI_USAGE.md) records tool corrections and distinguishes my
confirmed core review from code authorship and automated execution. Historical
reports and timestamps remain unchanged.

## Verdict and submission

- [Two-page release note](output/pdf/Soup-DevOps-Release-Note.pdf) and [source](docs/NOTE.md)
- [Reflection](docs/REFLECTION.md) and [email draft](docs/SUBMISSION_EMAIL.txt)
- [Manual RTX 5090 lab and screenshot](docs/GPU_LAB_RESULTS.md#supporting-screenshot)
- [Application summary, resume bullets, and technical discussion notes](docs/application-notes.md)
- [Evidence ledger](evidence/README.md) and [review resolutions](docs/reviews/RESOLUTIONS.md)

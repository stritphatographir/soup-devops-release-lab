# Verification report

## Current local documentation review

These checks were run by Codex against the documentation working tree based on
`67ccff1`, before the subsequent local submission commits. The applicant's newly confirmed core review and involvement are
recorded separately in [AI_USAGE.md](AI_USAGE.md#personal-technical-verification).
These executions are not attributed to the applicant.

| Check run now | Result | Scope |
| --- | --- | --- |
| Unit tests and coverage | PASS: 107 tests, 96.15% | Windows Python 3.13.14; coverage measures 44 application statements and eight branches, excluding `__main__.py`, not all release scripts/workflows |
| Lint | PASS | Ruff over the repository |
| Types | PASS: zero errors/warnings | Pyright over `src` with the explicit project interpreter |
| Workflow syntax | PASS | Existing actionlint executable; shellcheck/pyflakes integrations disabled because they are unavailable locally |
| Local distribution build | PASS | New output directory; sdist then wheel; source identity `local-uncommitted` |
| Clean installed consumers | PASS: wheel and sdist | Fresh venvs outside the checkout on Windows Python 3.13.14; no new Linux/macOS matrix claim |
| README CLI example | PASS | Installed local wheel in a separate fresh venv; `examples/service.toml` produced the documented JSON |
| Documentation | PASS | Current local links/anchors and referenced evidence checked; `git diff --check`; regenerated note visually inspected at two pages |

The unit/quality run started at `2026-11-12T15:07:40.073110+00:00`. Raw command output
is retained locally under `.tools/current-docs-audit/` (ignored scratch output,
not a replacement for the historical evidence below).

Not repeated in this review: full Docker/fault reproduction, the hosted native
matrix, advisory audits, publication or public read-back, provenance signature
verification, or GPU execution. Their historical results and limitations remain
separate. No code defect was established by the inspection; code, workflows,
locks, recorded evidence, tags, and the published release were not changed.
No commit, push, deployment, application, or email was made as part of those checks.

## Subsequent applicant-run GPU lab

After the local documentation review above, the applicant manually ran the
separate [RTX 5090 lab probe](GPU_LAB_RESULTS.md) and supplied terminal output.
Codex supplied the test and reviewed that output without SSH access. Reported
results were: no-GPU control exit 1; 65,536 vector-add results matching a CPU
reference with exit 0; no remaining positive-test container and a return to
2 MiB used/32,110 MiB free; CPU-only timeout control exit 124 with no remaining
container. The source/image/binary hashes and the trailing unmatched-parenthesis
paste error are recorded in the report.

This is user-reported manual execution, not a new Actions run or an independently
retrieved host log. It does not establish application GPU coverage, framework or
model correctness, benchmark speed, peak memory, provider billing, SIGKILL-path
or hung-driver recovery, or the proposed GPU CI broker/watchdog controls.

## Historical implementation and release evidence

Local checks: **PASS**. Hosted red/green evidence: **VERIFIED**.
Final verifier revision `feb2268`: **VERIFIED**, all 19 fixed jobs passed and
all four fresh fault runs failed in the required consumer with the intended
signature; their source-quality jobs all passed.
TestPyPI OIDC publish and public read-back: **PASS**. The
[v0.9.4 release](https://github.com/stritphatographir/soup-devops-release-lab/actions/runs/43224278803)
at `9ab7279` passed all 21 jobs, including the full checks, publication, and
fresh Linux Python 3.10 consumers of both public distribution formats.

| Phase | Result | Evidence and scope |
| --- | --- | --- |
| Build | PASS | Fresh 0.9.3 fault fixtures and 0.9.4 fixed wheel/sdist built. Both formats ran from clean consumers on Linux 3.10/3.12 and Windows 3.13. |
| Types | PASS | Pyright over src, targeting Python 3.10, using the explicit project interpreter: zero errors. This is package type coverage, not a claim that every test/helper is type checked. |
| Lint | PASS | Ruff over source, helpers and tests; actionlint over all five workflows. Local shellcheck/pyflakes were unavailable; the actual Bash tag guards are executed by adversarial tests. |
| Tests | PASS | 107 passed, zero skipped, 96.15% combined package line/branch coverage. The later annotation-only correction passed all 50 release-guard tests. |
| Security | PASS for executed checks | Both locked dependency sets audited with no known advisories. Credential-pattern search found no keys in deliverables. Initial vulnerable pins and their failed audit remain recorded. This does not establish absence of unknown vulnerabilities. |
| Diff | PASS | Runtime/workflow changes reviewed against both AI reports; git diff --check passed. Raw logs retain whitespace as evidence. |

Sources of evidence:

- `evidence/local/after-review-quality/`: commands, raw output and exit codes.
- `evidence/local/reproduction-after-review/`: all four failures and six fixed consumers.
- `evidence/actions/acceptance-55b79e0/`: actual run/job metadata and full logs.
- `evidence/actions/acceptance-feb2268/`: the stronger verifier's fixed and fault regressions.
- `evidence/actions/testpypi-release/`: successful release metadata and logs,
  tested artifact manifest, public-file hashes, provenance fields, and a fresh
  Windows Python 3.13 Simple Index wheel consumer.
- `evidence/actions/testpypi-publisher-registration.json`: observed matching OIDC mapping.
- `docs/reviews/`: original reviews, implementation report and resolution ledger.

The hosted fixed run passed 19 jobs, including all 15 native OS/Python consumer
combinations and a Docker runtime built from that same Actions artifact ID.
The four naive runs are genuinely green; the four hardened runs are genuinely
red, with source-quality green and the expected failed consumer/error signature.
Initial GitHub startup failures had no jobs and are recorded separately.

The public wheel and sdist hashes match artifact ID `13948045249`, the exact
artifact tested before publishing. The Windows consumer verified the downloaded
wheel hash before installation and passed `pip check`, isolated import,
version, and CLI checks. Runtime dependencies were bootstrapped from hash locks
on canonical PyPI; the candidate came only from TestPyPI, without a mixed index.
Public provenance fields identify the expected GitHub repository, workflow,
environment, filenames and digests. This is an identity/digest inspection, not
independent cryptographic signature verification.

There is no real-PyPI publisher or GPU rental in this repository. Independent
human review, repository governance/recovery controls, and a durable release
circuit breaker remain prerequisites for unattended production publication.

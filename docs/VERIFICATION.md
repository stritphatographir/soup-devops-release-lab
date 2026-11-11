# Verification report

Local checks: **PASS**. Hosted red/green evidence: **VERIFIED**.
Final verifier revision `feb2268`: **VERIFIED**, all 19 fixed jobs passed and
all four fresh fault runs failed in the required consumer with the intended
signature; their source-quality jobs all passed.
TestPyPI OIDC publish and read-back: **NOT PERFORMED**, account login/registration
still required. The assignment is not represented as fully accepted until that
target check succeeds.

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
- `docs/reviews/`: original reviews, implementation report and resolution ledger.

The hosted fixed run passed 19 jobs, including all 15 native OS/Python consumer
combinations and a Docker runtime built from that same Actions artifact ID.
The four naive runs are genuinely green; the four hardened runs are genuinely
red, with source-quality green and the expected failed consumer/error signature.
Initial GitHub startup failures had no jobs and are recorded separately.

Next required target check: after the account owner finishes the TestPyPI
pending-publisher registration, push a reviewed version tag and require both
OIDC publication and hash-verified public read-back to pass. There is no
real-PyPI publisher or GPU rental in this repository.

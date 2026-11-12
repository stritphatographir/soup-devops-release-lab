# Application and interview notes

## Project summary

Soup DevOps is a Python release lab built around `soup-check`, a small TOML-to-JSON
CLI. It contrasts source-only CI with clean installations of built distributions:
four isolated faults pass the naive checks but fail the intended installed
consumer. The fixed release tests one wheel/sdist bundle across Python 3.10–3.14
on Linux, Windows, and macOS, then publishes the tested bytes to TestPyPI through
OIDC and checks the public downloads. See the [implementation](../src/soup_release_lab/cli.py),
[workflows](../.github/workflows/checks.yml), and [evidence ledger](../evidence/README.md).

## Resume bullets

- Reviewed the core parts and remained involved throughout development of an
  AI-generated Python release lab demonstrating four packaging/compatibility
  failures that pass naive CI and fail clean installed consumers.
  [Fault fixtures](../scripts/inject_bug.py) | [recorded comparisons](../evidence/README.md#verified-hosted-red-and-green-evidence)
- The project demonstrates one wheel/sdist bundle tested across 15 native
  OS/Python combinations and Docker, then published to TestPyPI using OIDC and
  verified through public read-back; the recorded release passed 21 jobs.
  [Matrix](../scripts/matrix_plan.py) | [release workflow](../.github/workflows/release.yml) | [release snapshot](../evidence/actions/testpypi-release/run.json)
- Personally executed a separate AI-generated CUDA probe on an owned RTX 5090,
  checking 65,536 vector-add results against a CPU reference, expected failure
  without GPU access, and a CPU-only timeout/cleanup control.
  [Manual lab results and scope](GPU_LAB_RESULTS.md)

Historical package results include 107 passing tests and 96.15% combined
application-package line/branch coverage, plus a 19-job fixed workflow.
Those are agent/Actions executions, not personal package-test or production
claims. The separate lab execution is attributed to the applicant from the
terminal output shared in the conversation.
[Historical test output](../evidence/local/after-review-quality/unit-tests.txt) |
[fixed-run evidence](../evidence/README.md#final-verifier-regression-at-feb2268)

## Role and AI use

AI agents generated the implementation. I reviewed the core parts and remained
involved throughout development. I requested additional OpenCode and Antigravity
reviews, completed account login and verification, and flagged the wrong GitHub
commit identity. Codex implemented and coordinated checks; OpenCode reviewed the
pipeline and implemented verifier fixes; Antigravity completed an initial review,
while its follow-up stalled and a retry hit a provider quota error. The recorded
historical package-test executions were performed by agents and GitHub Actions.
I subsequently ran the separate AI-generated GPU lab commands myself and shared
their output; Codex did not use SSH. This does not imply that I authored particular
components, made every design decision, or independently validated every result. See the [AI-use disclosure](AI_USAGE.md)
and [review resolutions](reviews/RESOLUTIONS.md).

## Likely interview questions and technical talking points

Use the points as discussion scaffolding, with the linked code and evidence open.

### Why could the naive pipeline be green while users received a broken package?

- Its Linux library tests do not exercise every declared Python version, native
  Windows startup, installed package data, or the generated console command.
- The four faults are an unconditional `tomllib` import on Python 3.10, a Unix-only
  `pwd` import on Windows, omitted `defaults.json`, and an entry point naming
  `missing_main`. A successful build alone does not resolve or launch that entry
  point.
- Read: [naive workflow](../.github/workflows/naive.yml), [naive tests](../tests/naive/test_core.py),
  [fault injector](../scripts/inject_bug.py), [red/green records](../evidence/README.md#verified-hosted-red-and-green-evidence).

### What makes an installed-consumer check different from a source test?

- A fresh venv lives outside the checkout; `PYTHONPATH` and `PYTHONHOME` are
  removed, isolated Python is used, and the import path must resolve inside the
  consumer venv. This guards against accidentally reading the source tree.
- Both wheel and sdist are installed. Checks exercise `pip check`, the console
  command and module entry point, version identity, valid configuration, and
  expected failure exits. The sdist path also exercises its build requirements.
- Read: [consumer harness](../scripts/smoke_artifact.py),
  [local reproduction summary](../evidence/local/reproduction-after-review/summary.json).

### Why test 15 environments, and what does 96.15% coverage establish?

- Five advertised Python minors times three native operating systems gives 15
  fixed-release legs. The matrix validator requires the full fixed support
  contract and rejects a fault matrix missing the environment that exposes it.
- The historical 96.15% measures 44 package statements and eight branches, with
  `__main__.py` omitted. It does not measure workflow/helper coverage or prove
  compatibility. Architecture, runner image, locale, dependency combinations,
  and real user behavior remain limits.
- Read: [matrix planner](../scripts/matrix_plan.py), [matrix tests](../tests/test_matrix_plan.py),
  [coverage output](../evidence/local/after-review-quality/unit-tests.txt), [coverage boundaries](SECURITY.md).

### How does the release publish the bytes that were tested?

- Build once; carry the same-run Actions artifact ID to native consumers, Docker,
  and the publisher. Check source SHA, filenames, metadata, tag/version equality,
  and SHA-256 values against the manifest before testing and publishing.
- Public read-back checks the allowed file set and hashes, then installs both
  public distributions. It catches changed or unexpected public bytes; it occurs
  after publication, so a failure cannot undo the upload.
- Reusing tested bytes establishes artifact continuity. Setting
  `SOURCE_DATE_EPOCH` in the build does not demonstrate that an independent build
  reproduces those bytes.
- Read: [bundle verifier](../scripts/bundle.py), [release workflow](../.github/workflows/release.yml),
  [build script](../scripts/build_release.py), [read-back](../scripts/read_back.py), [tested manifest](../evidence/actions/testpypi-release/manifest.json),
  [public file records](../evidence/actions/testpypi-release/public-files.json).

### What do hash locks and dependency metadata checks protect against?

- Bootstrap installs use one explicit canonical index, exact locks and hashes,
  fresh venvs, and no pip cache. The candidate installs with `--no-deps --no-index`;
  `pip check` exposes incompatible or missing installed requirements.
- Preinstalled dependencies could hide a missing declaration, so wheel/sdist
  metadata must also declare the exact `Requires-Python` and marked `tomli`
  requirement. A hash identifies chosen bytes, not whether they are safe;
  ordinary downstream users do not automatically inherit these locks.
- Read: [consumer installation](../scripts/smoke_artifact.py), [metadata verifier](../scripts/bundle.py),
  [dependency-drift tests](../tests/test_release_guards.py), [initial failed audit](../evidence/local/initial-dependency-audit.txt).

### What does OIDC solve, and what does it leave open?

- Only the tag-triggered publisher receives `id-token: write`. The privileged job
  has no source checkout, dependency installation, or rebuild; it verifies the
  bundle with inline standard-library code and invokes the pinned publisher.
- This avoids a long-lived TestPyPI API token. A compromised authorized workflow
  or maintainer can still publish malicious bytes. Provenance identity/digest
  fields were inspected; independent cryptographic signature verification was
  not performed.
- Read: [publisher job](../.github/workflows/release.yml), [PR permissions](../.github/workflows/ci.yml),
  [publisher mapping](../evidence/actions/testpypi-publisher-registration.json), [provenance summary](../evidence/actions/testpypi-release/provenance-summary.json).

### How were the release guards themselves checked?

- Tests execute the actual workflow's inline verifier against adversarial
  bundles, including optimized Python, and compare its verdict with the consumer
  verifier. Explicit failures remain active when Python assertions are disabled.
- Tests cover stale commits, empty or mismatched tags, changed bytes, extra files,
  and metadata drift. Two verifier implementations still create maintenance
  risk; agreement is established only for the covered cases.
- Read-back unit tests cover public file-set rules, including partial visibility
  and duplicate entries. Hosted release evidence records download/install
  execution; these unit tests do not cover that whole orchestration.
- Read: [publisher verifier tests](../tests/test_publish_verifier.py),
  [tag and metadata tests](../tests/test_release_guards.py), [workflow extraction](../tests/workflow_source.py),
  [read-back unit tests](../tests/test_read_back.py), [release log](../evidence/actions/testpypi-release/run-log.txt).

### What did the additional AI reviews change?

- OpenCode identified Docker testing a separate build and gaps in tag identity,
  explicit failures, dependency metadata, and public file checks. Codex corrected
  Docker artifact identity; OpenCode implemented verifier fixes, followed by
  Codex-run regression checks.
- Antigravity's initial review led to evidence and GPU budget/cleanup/control
  clarifications. Its incomplete follow-up is recorded. The artifact-download
  permission concern did not reproduce in hosted runs. These are agent review
  outcomes, not claims that I personally discovered or implemented each fix.
- Read: [OpenCode review](reviews/OPENCODE.md), [Antigravity review](reviews/ANTIGRAVITY.md),
  [resolution ledger](reviews/RESOLUTIONS.md).

### Would you enable unattended real-PyPI publishing now?

- The project demonstrates automated TestPyPI publication; no real-PyPI publisher
  is configured. Source, workflow, manifest, and collected evidence share a trust
  domain. Hash agreement does not establish that an authorized build is benign.
- Priorities are independent review and protections for source, locks, workflows
  and tags, verified account recovery, then a durable release circuit breaker.
  The current stop-further-releases procedure is manual; failed read-back does
  not automatically block subsequent tags.
- Read: [threat model and fix order](SECURITY.md), [publishing procedure](PUBLISHING.md).

### Where would GPU checks fit, and what has actually run?

- Automated GPU CI remains design only. The CLI is CPU-only; the proposal
  gates a future CUDA component after CPU checks and before publication.
- I separately ran an AI-generated lab probe on my owned RTX 5090: a kernel
  produced 65,536 results matching a CPU reference (exit 0); the no-GPU control
  failed (exit 1); a CPU-only timeout control returned 124. Empty container
  listings and the reported GPU-memory baseline supported normal cleanup.
- These are user-reported manual results. They do not establish framework/model
  correctness, app GPU coverage, performance, peak memory, SIGKILL-path or
  hung-driver recovery, or a working cloud provisioning/watchdog service.
- The $8.76/month figure remains an assumption-based RTX 4090 rental estimate.
  An owned RTX 5090 experiment does not validate it. The proposal still needs
  cancellation, budget, startup, and provider-failure experiments.
- Read: [lab report and source](GPU_LAB_RESULTS.md),
  [GPU CI design, budget, and limitations](GPU_CI.md).

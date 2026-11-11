# OpenCode review: artifact identity, release gates, consumer coverage

Reviewer: OpenCode (Orca worker, task `task_7d9200f63ac9`), 2026-11-12.
Scope given to me: `.github/workflows/checks.yml`, `.github/workflows/release.yml`,
`scripts/bundle.py`, `scripts/build_release.py`, `scripts/smoke_artifact.py`,
`scripts/read_back.py`, and four questions — is the tested artifact the published
artifact, do tag/SHA checks fail closed, can a fork PR get publishing identity,
and does clean consumer coverage really reject the four injected bugs. Brief:
`Soup-Task-03-DevOps-Engineer(1).pdf`.

## What I actually reviewed, and how

| Item | Value |
| --- | --- |
| Local checkout HEAD | Started at `d08659a6a8100672f30f34b05f1e3777a54d6ebc` ("Build release lab with reproducible packaging faults and hardened artifact gates") with uncommitted edits; **moved to `8e0aa1b28ae6c604918d781804628cd9624e1898` ("Tighten index acceptance and preserve cross-platform fixture checks") while I was working**, which is also `origin/main` |
| What `8e0aa1b` adds over `d08659a` | Line-ending normalisation + `.gitattributes`; the single-step `python310` injector (`scripts/inject_bug.py:38-45`); `scripts/read_back.py:17-21` `public_files_ready()`; `tests/test_read_back.py`; `.github/workflows/service-probe.yml`; a per-tag `concurrency` group (`release.yml:10-13`) |
| Line numbers below | Cited against **HEAD = `8e0aa1b`**, and marked "at `d08659a`" where a line only existed there |
| Revision the queued Actions runs use | `8e0aa1b` (the eight completed runs used `head_sha=d08659a`) |
| Host used for probes | Windows 11, Python 3.13.14, the repo's own `.venv` (pytest 9.2.0, ruff 0.17.4, pyright 1.1.414, build 1.6.1, setuptools 84.2.1, wheel 0.48.0) |

I read the code and evidence, then re-ran the gates myself rather than trusting
the logs: ruff, pytest+coverage, pyright, `inject_bug` for all five modes,
`build_release` with matching and mismatching tags, `bundle.py` with correct /
wrong / empty `--source-sha` and `--tag`, clean wheel and sdist consumers for each
fixture, and the `release.yml` publish-job inline gate (copied verbatim into a
scratch file) against a correct bundle, a wrong SHA, `-O`, a malformed tag, a
missing `manifest.json`, and a METADATA-only drift. Probe scripts and JSON dumps
live outside the repo in `C:/Users/amirt/AppData/Local/Temp/opencode/`
(`review-probe-a.py`, `-b.py`, `-c.py`, `review-A/probe-a.json`,
`review-B/probe-b.json`, `review-B/probe-c.json`). **They are ephemeral and not
part of the submission.** The only file I wrote in the repository is this one.
I also ran `.tools/actionlint.exe` (exit 0), `git ls-remote --tags` for every
action pin, read-only GitHub REST calls, and `git fetch --no-tags origin main`
(this last one wrote `FETCH_HEAD`/remote refs only; no branch, index, or working
tree change).

## Verdicts on the four questions

| Question | Verdict |
| --- | --- |
| Is the tested artifact the published artifact? | **Yes for the Actions path** (one artifact ID, no name lookups). **No for the Docker path**, which verifies a different build (F1). |
| Do tag and SHA checks fail closed? | **Mostly yes** (measured). **One fail-open shape: an empty value disables the gate instead of erroring** (F2). The publish-time gate is a weaker duplicate of the check-time gate (F3) and is stripped by `-O` (F4). |
| Can a fork PR get publishing identity? | **No** — nothing found, at either revision (F5 lists the two things that remain server-side and unverifiable). |
| Does clean consumer coverage really reject the four injected bugs? | **Yes as written, and 3 of 4 reproduced on this host**; the guarantee rests on an untested coupling between the fault list and a hardcoded matrix expression (F6), and the fourth (`python310`) is only demonstrable on 3.10. |

## Measured probe matrix

Exit code `0` = gate passed, `1` = failed as intended. Full records in
`review-B/probe-b.json` and `review-B/probe-c.json`.

| Probe | fixed | python310 | windows | missing-data | entrypoint |
| --- | --- | --- | --- | --- | --- |
| `build_release.py --tag v9.9.9` | 1 | 1 | 1 | 1 | 1 |
| `bundle.py --source-sha <wrong>` | 1 | 1 | 1 | 1 | 1 |
| `bundle.py --tag v9.9.9` | 1 | 1 | 1 | 1 | 1 |
| `bundle.py --source-sha "" --tag ""` | **0** | **0** | **0** | **0** | **0** |
| `smoke_artifact.py --kind wheel` (host 3.13) | 0 | **0** | 1 | 1 | 1 |
| wheel METADATA rewritten to `9.9.9`, manifest re-hashed → `bundle.py` | 1 | 1 | 1 | 1 | 1 |
| same bundle → `release.yml` inline gate | **0** | **0** | **0** | **0** | **0** |

Inline `release.yml` gate on the fixed bundle: correct env `0`; wrong SHA `1`
(`AssertionError`, `release.yml:49`); wrong SHA **with `-O`** **`0`** ("Exact tested release
bundle verified."); wrong SHA with `PYTHONOPTIMIZE=1` in the environment and no
`-O` `1`; tag `v1` `1`; missing `manifest.json` `1` (also `1` under `-O`, because
that one is not an `assert`). `smoke_artifact.py --kind sdist` on the fixed
bundle: `0` ("PASS: clean sdist consumer on win32 / Python 3.13.14").

Local quality gates, both revisions: `ruff check .` exit 0; `pytest --cov
--cov-branch` 35 passed / 96.15% on `d08659a`, 38 passed / 96.15% on `8e0aa1b`
(`[tool.coverage.report] fail_under = 85`, `pyproject.toml:47`); `actionlint`
exit 0.

## Findings

### F1 — Medium — the Docker lane verifies a *different build* than the published artifact

`Dockerfile:12` runs `python scripts/build_release.py --out /release` inside the
`build` stage, and `Dockerfile:17-18` (`verified`) plus `Dockerfile:22-26`
(`runtime`) consume that in-image result. The published bytes come from
`checks.yml:69-79`, a separate build in a different job. Nothing compares the
Docker-built digests with `manifest.json` from the uploaded artifact, and inside
Docker `--source-sha` falls back to `os.environ.get("GITHUB_SHA",
"local-uncommitted")` (`scripts/build_release.py:21`), so the Docker manifest
binds the bundle to **no commit at all**.

Impact: "Verify distributions in Docker" (`checks.yml:123-124`) and the
unprivileged runtime launch (`checks.yml:125-128`) prove the *recipe* is sound,
not that the published wheel is the one that launches. `SECURITY.md:12` claims
"same-run artifact ID" as the stale-artifact control, which is true for
`consumers`/`publish`/`read-back` but not for the Docker lane, and the docs do
not carve that out.

Suggested direction (coordinator's call): have the Dockerfile take the CI
artifact (or its `manifest.json`) as a build input and fail if the in-image build
digests differ, or state explicitly in `Dockerfile`/`SECURITY.md` that the Docker
lane is a recipe check on a locally-built bundle.

### F2 — Medium — tag and SHA gates are skipped, not failed, when the value is empty

`scripts/bundle.py:19-21` returns immediately when `tag` is falsy;
`scripts/bundle.py:67` skips the SHA comparison when `source_sha` is falsy;
`scripts/build_release.py:22` defaults `--tag` to `""`. Measured: a valid 0.9.4
bundle with `--tag v9.9.9` exits 1, but the same bundle with `--tag ""` exits 0.

In `checks.yml:103-107` those values arrive as `${{ inputs.release-tag }}`
(declared optional with `default: ''`, `checks.yml:9-11`) and `$GITHUB_SHA`. On a
branch or PR run the empty tag is intentional, but the same emptiness means a
renamed or dropped input on the release path would silently *remove* the tag gate
from every consumer leg instead of erroring. Blast radius is limited —
`release.yml:49-51` recomputes the tag check from `github.ref_name` inside the
publish job — so the published artifact is still bound, but `SECURITY.md:14`
("exact `vMAJOR.MINOR.PATCH` equality") is effectively enforced in one place
rather than two.

Suggested direction: make `release-tag` `required: true` in
`on.workflow_call.inputs` (and have `ci.yml` pass `''` explicitly), or make
`bundle.py`/`build_release.py` treat a present-but-empty `--tag` /
`--source-sha` as an error, and add a test for the empty case (today
`tests/test_release_guards.py:60-63` only covers non-empty bad tags).

### F3 — Medium — the publish-time gate is an independent, strictly weaker copy of the check-time gate

`release.yml:43-61` re-implements `bundle.verify_manifest` inline (reasonable:
the publish job deliberately does no checkout, `release.yml:31-37`). It is not
equivalent: it never opens the wheel or sdist, so it cannot see
name/version metadata. Measured with a bundle whose wheel METADATA says `9.9.9`
while the manifest and tag say `0.9.4` and whose hashes are recomputed to match:
`bundle.py` exits 1 (`ValueError: artifact metadata mismatch`), the inline gate
exits 0 and prints "Exact tested release bundle verified." No test asserts the
two implementations agree, so drift is silent — and one of the two
("validates it using inline standard-library code", `SECURITY.md:24-26`) is
described as a re-validation of what was already verified.

Also unchecked by both: that the distribution **filename** version matches
METADATA (both compare METADATA to `manifest["version"]` only,
`bundle.py:53` and `:80`); that is left to PyPI's own acceptance rules.

Suggested direction: upload `scripts/bundle.py` alongside `manifest.json` and
`dist/` (the upload path is already `$RUNNER_TEMP/release/`, `checks.yml:77`, and
`bundle.py` is pure stdlib), so the publish job runs the *same* verifier instead
of a paraphrase; or keep two implementations and add a test that feeds both the
same fixture and requires the same verdict.

### F4 — Low — the publish gate is `assert`-based and disappears under `-O`

Measured: `python -I -O inline_gate.py` with a deliberately wrong `EXPECTED_SHA`
exits 0. Mitigating fact I also measured: `python -I` implies `-E`, so
`PYTHONOPTIMIZE=1` alone (no `-O` flag) does **not** strip the asserts — the same
run exits 1. So the exposure needs someone to add `-O`/`-OO` to `release.yml:43`,
which is a plausible "speed it up" edit. `release.yml:47-59`
could use explicit `if not …: raise SystemExit(...)` for the four assertions that
carry the trust.

### F5 — Info — fork PRs cannot reach a publishing identity (nothing found)

Verified at `d08659a` **and** at HEAD (`8e0aa1b`):

- Only `release.yml` can publish, and only on `push: tags: ['v*']`
  (`release.yml:3-5`); a fork cannot create a tag in this repository.
- `id-token: write` occurs exactly once in `.github/workflows/` —
  `release.yml:30` — on the `publish` job, which does
  no checkout, no install, and no build (`release.yml:31-37`).
- No workflow references `secrets.*`, `GITHUB_TOKEN`, `pull_request_target`, or
  `workflow_run`; every workflow declares `permissions: contents: read`
  (`checks.yml:17-18`, `ci.yml:16-17`, `naive.yml:13-14`, `release.yml:7-8`);
  every checkout uses `persist-credentials: false`.
- The publish job's environment is `testpypi` (`release.yml:25-27`), matching the
  pending-publisher registration documented in `docs/PUBLISHING.md:11-18`.

Two things I could not verify, and the repo should keep saying so
(`SECURITY.md:33-37` does): the `testpypi` environment's tag-only deployment rule
and the PyPI pending-publisher registration are server-side state —
`.tools/environment.json` and `.tools/tag-policy.json` are local snapshots, not
proof. Separately, `ci.yml:7` runs `pull_request`, so on fork PRs the Docker job
(`checks.yml:115-128`, which only skips when `bug != 'fixed'`) builds a
fork-authored `Dockerfile`; the container run is
`--network none --read-only --cap-drop ALL --security-opt no-new-privileges` and
the token stays read-only, so this is a cost/abuse surface, not an identity leak.

### F6 — Medium — "each fault is seen by at least one consumer leg" is load-bearing and untested

The fault-mode matrix is one inline expression: `checks.yml:90` gives three legs
(`ubuntu/3.10`, `ubuntu/3.12`, `windows/3.12`) unless `inputs.bug == 'fixed'`, in
which case it gives 15. My host measurements show why each leg is mandatory: the
`python310` fixture **passes** a clean wheel consumer on 3.13 (exit 0 — only the
3.10 leg sees it), and `from pwd import getpwuid` succeeds on Linux, so the
`windows` fixture is visible only on the `windows-latest` leg. Nothing enforces
that mapping: `bug` is an unvalidated `type: string` in the reusable workflow
(`checks.yml:6-8`), and no test enumerates fault → leg. A fifth fault that only
breaks on 3.13 or macOS, or an edit to that one JSON expression, produces a
false-green **fault** run — the exact evidence the brief asks for — while the
fixed run stays green and hides it. (Unknown names do fail closed:
`inject_bug.materialize` raises on anything outside `BUGS`,
`scripts/inject_bug.py:23-24`.)

Suggested direction: an explicit `BUG_LEGS` mapping in `inject_bug.py` (or a
`required-python`/`os` attribute per fault) plus a unit test that asserts the
matrix in `checks.yml` covers it, or a guard step that fails when the selected
fault's required legs are absent from `strategy.matrix`.

### F7 — Medium — the remote half of the evidence is still zero successful runs

As of my check, the repository is 1 day old (`created_at 2026-11-11T20:38:33Z`)
and has 12 Actions runs total: 8 completed with
`conclusion=startup_failure`, `job_count=0`, `head_sha=d08659a`
(`evidence/actions/startup-failures/runs.json`), annotated only with GitHub's
generic "An unexpected error has occurred" text and request id
`810c278f-de10-11f1-83a1-db5e1400e64b`
(`evidence/actions/startup-failures/annotation.txt`); 4 more were `queued`,
including an `Actions service diagnostic` probe (`.github/workflows/service-probe.yml`,
committed in `8e0aa1b`). There is no successful run, no red-per-fault run, no
publish, and no TestPyPI read-back yet.

Impact on grading: the brief's deliverable is *links to Actions runs (red and
green)*. Everything supporting the naive-vs-hardened contrast right now is local
Docker/Windows output under `evidence/local/`. That is honest work and
`evidence/README.md:5-7` says so, but it is not the deliverable, and it should
not be presented as if it were. Related wording: `docs/AI_USAGE.md:3-5` says the
assistant "executed the recorded local and GitHub checks"; the GitHub executions
on record are eight scheduler failures with no job logs. And `evidence/README.md`
still says Actions URLs "will be added", while the URLs (all negative) already
exist one directory down — the ledger should link the startup failures
explicitly, because a clear negative beat a quiet success.

### F8 — Low — the preserved `python310` log no longer matches the deployed injector

`evidence/local/reproduction-1/python310-hardened.txt` shows the failure at
`cli.py`, line 6, matching the two-step injector in `d08659a` (`replace_once(...,
"", ...)` plus `import sys\nimport tomllib\n`). The injector at HEAD (`8e0aa1b`,
`scripts/inject_bug.py:38-45`) replaces the `try/except` in one step,
so the fault now lands at `cli.py` line 9 (verified by materialising the current
fixture). Same failure mode and the same signature string, but the preserved log
quotes a line number that no longer exists, and **no log in the repo was produced
by the currently deployed injector.** I confirmed the current fixture keeps the
naive side green on this host: `ruff check .` exit 0 and the unit suite passes
(the insertion point also is not an import-sorting problem for ruff — measured).
Re-run the `python310` pair after the fault demo runs land on `8e0aa1b`.

### F9 — Low — the consumer lane cannot see an undeclared runtime dependency

`scripts/smoke_artifact.py:44` installs `requirements/runtime.lock` into the
fresh consumer venv **before** the artifact is installed `--no-deps --no-index`
(`:47`), and `pip check` (`:49`) then validates the artifact's declarations
against a venv that already contains the lock's packages. On 3.10 the only
runtime dependency (`tomli==2.2.1; python_version < "3.11"`,
`pyproject.toml:12`) is present regardless of what the wheel declares, so a
dropped or mis-marked dependency line would stay green — and 3.10 is the only
version where that line matters. Not demonstrated at runtime here (no 3.10
interpreter on this host; Docker belonged to the coordinator during the review).
Cheapest close: assert that the artifact's `Requires-Dist` set equals the marked
subset of `requirements/runtime.lock`, in `bundle.py` next to the existing
metadata check.

### F10 — Low — `read-back` extra-file tolerance: closed at HEAD

At `d08659a`, `scripts/read_back.py:24` accepted a TestPyPI release whose file
list was a **superset** of the manifest (`set(manifest["files"]) <= {...}`), and
`:37-38` skipped any unexpected public file, so a version carrying an extra
untested distribution (a third wheel, a stale upload) would still pass
acceptance. HEAD (`8e0aa1b`) replaces that with `public_files_ready()`
(`scripts/read_back.py:17-21`, called at `:31`), which rejects unexpected names
and duplicate index entries, and it raises `ValueError` rather than retrying, so
a wrong index fails the run immediately instead of looping ten times. Covered by
`tests/test_read_back.py`; I ran the `8e0aa1b` suite: 38 passed, coverage 96.15%.
Worth keeping the negative case in the evidence ledger as an example of a gate
tightened by review.

### F11 — Low — small supply-chain and robustness edges worth one line each in the docs

- The Node runtime that executes pyright is outside `requirements/ci.lock`: the
  pinned `pyright==1.1.414` wheel resolves Node from the runner image, or fetches
  one through `nodeenv` (`.venv/.../pyright/node.py`) when `PYRIGHT_PYTHON_NODE_VERSION`
  is unset (it is). `SECURITY.md:15` already concedes runner images are outside
  control; naming the type-checker specifically is more useful.
- No workflow grants `actions: read`, yet three jobs call `download-artifact`
  (`checks.yml:98`, `release.yml:33`, `release.yml:80`). Upstream v8.0.2 docs say
  same-run downloads are in scope for the scoped token (and the artifact is
  always from the same run here, which is the good case), but "Resource not
  accessible by integration" reports under `contents: read`-only tokens are
  common enough that this should be the first thing to check if the queued runs
  fail at a download step. I could not settle it without a real run.
- The Types step depends on an easy-to-"simplify" flag: with
  `--pythonpath "$(command -v python)"` (`checks.yml:43`) pyright reports 0
  errors; without it, the same tree reports `Import "tomli" could not be
  resolved` (measured, 1 error). A comment beside the flag would protect it.
- `inject_bug.IGNORES` (`scripts/inject_bug.py:8-11`) decides what the *built*
  tree contains, and nothing compares the sdist's file list to the checkout, so a
  future entry could silently drop files from the published sdist.
- `release.yml:10-13` is now `group: testpypi-release-${{ github.ref }}`
  — per-tag serialisation, which is better than the old global group for pending
  runs, but two different tags pushed together may now publish in either order
  (TestPyPI accepts both; only version ordering is at stake).

### F12 — Info — claims I verified as true, so the coordinator need not re-check them

- Every action pin matches the version in its comment (`git ls-remote --tags`):
  `actions/checkout@3d3c42e…` = `v7.0.1`, `actions/setup-python@6d4fd22…` =
  `v7.1.0`, `actions/upload-artifact@cf430e0…` = `v7.0.2`,
  `actions/download-artifact@9000827…` = `v8.0.2`,
  `pypa/gh-action-pypi-publish@7245906…` = `v1.14.3` (commit, not tag object).
- `artifact-ids` is a real `download-artifact@v8.0.2` input, and single-ID
  downloads land directly in `path`, so the `manifest.json` + `dist/` layout that
  `bundle.py` expects is preserved. `merge-multiple: true` is inert for one ID.
  `digest-mismatch` defaults to `error`.
- The identity chain is real and has no name-based fallback:
  `checks.yml:54` (`steps.upload.outputs.artifact-id`) → `checks.yml:13-15`
  (workflow output) → `checks.yml:100`, `release.yml:35`, `release.yml:82`.
  Artifact name includes `sha`, `run_id`, `run_attempt` (`checks.yml:76`), and
  `if-no-files-found: error` (`checks.yml:78`).
- Same bytes end to end: `consumers` verifies, `publish` re-verifies hashes and
  immediately uploads `release/dist/` (`release.yml:62-67`), and
  `read_back.py:46-52` re-hashes the **bytes TestPyPI serves** against the same
  manifest, refusing non-HTTPS URLs (`:46-47`) before running both consumers
  again (`:54-55`). A missing `manifest.json` aborts (measured, even under `-O`).
- `build_release.py:25-26` refuses a pre-existing output directory (stale
  artifact), and the local fallback SHA `local-uncommitted` (`:21`) then fails
  the CI comparison rather than passing it (fail closed).
- `smoke_artifact.py:54-55` proves the import stayed inside the throwaway venv,
  and `:56-60` compares the installed CLI's `--version` with the distribution
  metadata — so a `__init__.__version__`/`pyproject` drift is a consumer failure,
  not a silent inconsistency.
- `read_back.py` retries the index but never retries an acceptance failure, and
  it recomputes SHA-256 itself instead of trusting TestPyPI's recorded digests.
- Fault evidence is internally consistent: every
  `evidence/local/reproduction-1/*-naive.txt` and `*-build.txt` records
  `Exit code: 0`, every `*-hardened.txt` records `Exit code: 1` with the expected
  signature (`summary.json` matches), and `python310-hardened.txt` fails at
  `soup-check --version` with `ModuleNotFoundError: No module named 'tomllib'`
  after `pip check` said "No broken requirements found" — the exact green-install
  / red-launch shape the brief describes.
- Fixture isolation is fail-closed (`scripts/inject_bug.py:25-28`, tested at
  `tests/test_release_guards.py:66-68`); my probes wrote only to a temp directory
  outside the checkout.
- The dependency-audit gate is meaningful, and its failure is kept:
  `evidence/local/initial-dependency-audit.txt` (6 advisories in the original
  pins, exit 1) and `checks.yml:44-45` audits `ci.lock`, which includes
  `build.in` and `runtime.in` contents via `requirements/ci.in:1`.

## Limits of this review

1. **Revisions.** I read the tree at `d08659a` plus its uncommitted edits, then
   reviewed the `d08659a..8e0aa1b` diff, because the branch moved during the
   review and HEAD is now `8e0aa1b` (= `origin/main`). My measurements of
   `bundle.py`, `build_release.py`, `smoke_artifact.py`, `inject_bug.py`,
   `checks.yml` and the inline publish gate apply unchanged to `8e0aa1b`;
   `read_back.py` and the `release.yml` concurrency group changed underneath me
   and are reported per-revision (F7, F8, F10, F11). While I worked, the
   coordinator also modified `docs/SECURITY.md` and `docs/GPU_CI.md` and added
   `docs/NOTE.md`, `scripts/render_note.py`, `requirements/docs.{in,lock}`,
   `output/` and more under `evidence/`; my `SECURITY.md` citations point at
   lines that are unchanged in both versions, and everything newer than my last
   read is unreviewed.
2. **No remote execution by me.** I did not publish, dispatch, re-run, or cancel
   anything, and did not read credentials. My GitHub calls were anonymous GETs
   plus `git ls-remote`/`git fetch`. I did **not** treat queued runs as
   successes — see F7.
3. **Platform gaps I could not close.** `python310` needs a 3.10 interpreter and
   the host has 3.13/3.14 only; Docker was in use by the coordinator, so I did
   not run the image builds. No 3.11/3.13/3.14 legs, no macOS legs, and no
   Windows-*runner* legs were exercised (my Windows result came from a native
   consumer run, not a GitHub Windows runner). The 15-job fixed matrix
   (`checks.yml:90`) and its `timeout-minutes: 15` (`:84`) remain unproven at
   scale; on this host a wheel consumer and a sdist-rebuild consumer each
   finished well inside a minute, so the risk is runner variance rather than a
   design defect.
4. **Server-side state is unverifiable from a clone**: branch and tag
   protection, the `testpypi` environment and its tag rule, the PyPI pending
   publisher, and the retention of failed runs.
5. **Probe scope.** My probes used the repo's own `.venv` (Python 3.13.14) and
   live PyPI for the lock installs; they reproduce the *consumer* logic, not the
   Actions runner environment. `pip check`'s behaviour on 3.10 (F9) is reasoned
   from `smoke_artifact.py:44-49`, not measured.
6. **Overlap with the other review.** `docs/reviews/ANTIGRAVITY.md` covers the
   GPU design and the document set. We agree that fork PRs reach no privileged
   context (their F7) and that the submission's remote evidence is outstanding
   (their F1, my F7); they did not have the Actions run data that F7 cites, and
   I did not re-check their cost arithmetic.

## Shortest list for the coordinator

1. Land the remote runs and record them honestly, startup failures included (F7).
2. Make the tag/SHA gates reject empty values instead of skipping (F2).
3. Close the publish-time gap: metadata check in the inline gate, and no
   assert-only trust chain (F3, F4).
4. Bind the Docker lane to the published artifact, or state that it does not (F1).
5. Make fault → matrix-leg coverage explicit and tested (F6), and re-run the
   `python310` pair against the deployed injector (F8).

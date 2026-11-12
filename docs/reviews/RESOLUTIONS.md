# Review resolution ledger

Two wording corrections matter when reading the historical review: avoiding
artifact-supplied code in the privileged job was the coordinator's security
design constraint, not an explicit sentence in the assignment brief. The initial
audit's six reported records include conditional-marker duplicates; they
describe three affected packages, not six independent vulnerabilities.

The original reviews are retained without rewriting their findings. They refer
to earlier revisions; this ledger records later work and actual acceptance.

| Finding | Resolution and evidence |
| --- | --- |
| Antigravity F1: missing evidence/note, overbroad AI claims | Actual red/green links and raw logs are in evidence/README.md. The rendered note is exactly two pages. AI_USAGE distinguishes assistant execution, applicant account steps, real hosted results, and successful OIDC publication/read-back. |
| Antigravity F2: GPU compatibility-set cost | The estimate explicitly assumes one supported software tuple; expanding N changes the release-minute formula. Host drivers are recorded rather than assumed replaceable. |
| Antigravity F3: concurrency | GPU release/nightly groups are separate in the design, and the broker enforces one live pod. Actual CPU/TestPyPI release attempts use a per-tag group. New GitHub docs support queue:max, but the installed actionlint does not yet accept it; the implemented workflow uses per-tag serialization. |
| Antigravity F4/F5: cleanup and budget | The design specifies termination, minute-by-minute reconciliation, heartbeat alerts, signed result URLs, ambiguous-create reconciliation, cold-start sensitivity, hosting assumptions, and a failure circuit breaker. It does not promise a provider-enforced hard spending cap. |
| Antigravity F6: fix-first order and release breaker | SECURITY.md ranks the prerequisites and identifies disabling later releases as a manual operational control. |
| OpenCode F1: Docker tested a different build | Actions now downloads the exact build artifact ID and uses Docker artifact-runtime. The green 55b79e0 Docker log verifies its source SHA and tests both distributions before launching the restricted runtime. Standalone source-image builds remain explicitly separate. |
| OpenCode F6: fault/matrix coupling | matrix_plan.py generates and validates the matrix. Adversarial tests remove required fault legs or add an undeclared fault and require rejection. The green fixed run and red fault runs at 55b79e0 execute this planner. |
| OpenCode F7/F8: missing hosted evidence and old injector logs | New runs at 55b79e0 use the current injector, with all four naive/source-quality passes and all four intended consumer failures. Earlier local logs remain as historical evidence. |
| OpenCode F10: public release could contain an extra wheel | public_files_ready rejects extra or duplicate filenames; adversarial tests cover an untested platform wheel and partial index visibility. |
| OpenCode F2/F3/F4/F9: verifier and dependency metadata | Implemented by OpenCode: explicit empty-identity rejection, mandatory tag/ref matching on tag-triggered checks, metadata-aware publish verification with no assertions, and exact dependency/Python-range policy. The actual workflow verifier is exercised against adversarial bundles and under optimized Python. The coordinator independently confirmed 107 passing tests, clean quality/audit checks, and a fresh full reproduction. The feb2268 fixed run then passed all 19 hosted jobs, and all four fresh fault runs failed in the required consumer with source-quality green. |

Known limits remain visible in SECURITY.md. TestPyPI release run `43224278803`
passed all 21 jobs at the immutable `v0.9.4` tag, including public wheel/sdist
read-back. Public hashes match the exact tested artifact; a fresh Windows
Simple Index wheel consumer also passed. Public provenance identity and digest
fields were inspected, without claiming independent cryptographic verification.
The applicant has not claimed an independent personal review or GPU execution.

The coordinator also corrected GitHub's error-annotation syntax in the tag
guards and reran all 50 release-guard tests successfully. Native same-run
artifact downloads with contents:read-only permissions already succeeded in
the 55b79e0 matrix and Docker jobs; the speculative permission concern in the
original review did not reproduce. Pyright's Node runtime remains a hosted
runner dependency outside the Python hash lock.

Antigravity's initial review completed. Its follow-up task stopped without a
completion report; the coordinator applied the documentation changes. After
reapplying hooks through the running Orca app, retry dispatch
`ctx_36bfb0162eec` reached an explicit provider quota error. The exact owned
worker was stopped with confirmed termination. No account upgrade, model
switch, or further quota retry was attempted. The failure remains part of the
tool-use record, separate from the successful initial review.

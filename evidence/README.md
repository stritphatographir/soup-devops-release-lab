# Evidence ledger

Repository: https://github.com/stritphatographir/soup-devops-release-lab

The local logs contain actual exit codes. Deliberately broken fixtures are
never published. **Required hosted red/green evidence is verified at 55b79e0;
TestPyPI publication remains unverified.** A startup failure is an infrastructure
failure, not proof of package-bug detection.

## Final verifier regression at feb2268

The final verifier implementation at `feb2268131637f283eaee5e95536835a84145b62`
passed [all 19 fixed jobs](https://github.com/stritphatographir/soup-devops-release-lab/actions/runs/43103313246),
including the 15-leg native matrix and exact-artifact Docker lane.
It also rejected every fault in a fresh hosted regression:

| Fault | Actual red run | Required consumer |
| --- | --- | --- |
| python310 | [failed as intended](https://github.com/stritphatographir/soup-devops-release-lab/actions/runs/43103713099) | ubuntu-latest, 3.10 |
| windows | [failed as intended](https://github.com/stritphatographir/soup-devops-release-lab/actions/runs/43103718608) | windows-latest, 3.12 |
| missing-data | [failed as intended](https://github.com/stritphatographir/soup-devops-release-lab/actions/runs/43103724109) | ubuntu-latest, 3.12 |
| entrypoint | [failed as intended](https://github.com/stritphatographir/soup-devops-release-lab/actions/runs/43103729733) | ubuntu-latest, 3.12 |

All four source-quality jobs passed. The collector required the error signature
inside the specific failed consumer's log, not merely elsewhere in the run.
[The snapshot and raw logs](actions/acceptance-feb2268/runs.json) record
`all_expected_outcomes_observed: true`. The naive comparison runs below use
55b79e0 and the unchanged four fault fixtures. No old result was overwritten.

## Verified hosted red and green evidence

All nine runs below used `55b79e0a285db3e9d5244d62b768200f8719eca2`.
The collector downloaded real job logs, required genuine run failures, matched
the expected error signature, and checked that the required OS/Python consumer
failed. All four source-quality jobs stayed green.

| Fixture | Naive: green | Hardened: red | Rejecting consumer and signature |
| --- | --- | --- | --- |
| python310 | [passed](https://github.com/stritphatographir/soup-devops-release-lab/actions/runs/43100255326) | [failed](https://github.com/stritphatographir/soup-devops-release-lab/actions/runs/43100260410) | Linux 3.10: missing tomllib |
| windows | [passed](https://github.com/stritphatographir/soup-devops-release-lab/actions/runs/43100265599) | [failed](https://github.com/stritphatographir/soup-devops-release-lab/actions/runs/43100269894) | Windows 3.12: missing pwd |
| missing-data | [passed](https://github.com/stritphatographir/soup-devops-release-lab/actions/runs/43100274474) | [failed](https://github.com/stritphatographir/soup-devops-release-lab/actions/runs/43100278631) | Linux 3.12: defaults.json missing |
| entrypoint | [passed](https://github.com/stritphatographir/soup-devops-release-lab/actions/runs/43100283422) | [failed](https://github.com/stritphatographir/soup-devops-release-lab/actions/runs/43100288844) | Linux 3.12: missing_main |

**Fixed green:** [all 19 jobs passed](https://github.com/stritphatographir/soup-devops-release-lab/actions/runs/43099378682).
This includes quality, matrix planning, one build, Docker using that exact
artifact ID and SHA, and all 15 native consumer legs. Each native leg tested
both wheel and sdist. The Docker log records the same source SHA and both clean
consumer passes before the restricted runtime launch.

The [full snapshot](actions/acceptance-55b79e0/runs.json) records
`all_expected_outcomes_observed: true`; raw logs are stored beside it. Reproduce
collection with `python scripts/collect_actions.py --plan
evidence/actions/acceptance-plan.json --out evidence/actions/a-new-directory`.
These baseline results precede the final verifier-hardening follow-up. Its
additional local and hosted acceptance is recorded above. TestPyPI publication
and read-back are the remaining target checks.

| Fault | Why naive checks pass | Required hardened failure |
| --- | --- | --- |
| `python310` | Linux 3.12 has `tomllib`; tests only call library helpers | Installed CLI on Python 3.10: missing `tomllib` |
| `windows` | Linux provides `pwd`; tests never load CLI | Native Windows installed CLI: missing `pwd` |
| `missing-data` | The JSON file exists in the source checkout | Installed wheel cannot read `defaults.json` |
| `entrypoint` | Tests call functions; building does not resolve console entry point | Installed `soup-check` points at `missing_main` |

`local/initial-dependency-audit.txt` records an additional real failure: vulnerable
initial tool pins. It is independent of the four intentionally introduced bugs.
Any infrastructure or integration failures encountered during verification will
be retained alongside the later fixed result.

## Executed local checks

The [first full reproduction](local/reproduction-1/summary.json) records four
naive passes, four successful builds, four consumer rejections for the intended
error, and six fixed wheel/sdist consumer passes. The raw logs next to the
summary preserve commands, stdout/stderr, and exit codes. Linux containers used
Python 3.10/3.12; native Windows used Python 3.13.14.

[Docker build](local/docker-runtime-build.txt) and
[restricted runtime launch](local/docker-runtime-launch.txt) succeeded.
The later hosted fixed run also exercised macOS and the full 15-environment
contract. Local executions and hosted executions are kept as distinct evidence.

After the verifier fixes, a [fresh full reproduction](local/reproduction-after-review/summary.json)
again recorded four naive/build passes, four intended consumer failures, and
six fixed consumers. [The updated quality records](local/after-review-quality/summary.json)
show 107 passing tests, 96.15% package coverage, clean lint/types/workflow checks,
and no known vulnerabilities in either CI or PDF-tool locks. Earlier logs remain
unchanged. The tag-annotation refinement was then checked with all 50 dedicated
release-guard tests.

## Actual Actions attempts at d08659a

All eight dispatches below returned `startup_failure`, each with **zero jobs**.
GitHub's annotation reported an unexpected internal error and supplied a support
request ID. These do not meet the assignment's requested green/red evidence.

| Fixture | Naive attempt | Hardened attempt |
| --- | --- | --- |
| python310 | [startup failure](https://github.com/stritphatographir/soup-devops-release-lab/actions/runs/43097507326) | [startup failure](https://github.com/stritphatographir/soup-devops-release-lab/actions/runs/43097510246) |
| windows | [startup failure](https://github.com/stritphatographir/soup-devops-release-lab/actions/runs/43097513455) | [startup failure](https://github.com/stritphatographir/soup-devops-release-lab/actions/runs/43097516453) |
| missing-data | [startup failure](https://github.com/stritphatographir/soup-devops-release-lab/actions/runs/43097519691) | [startup failure](https://github.com/stritphatographir/soup-devops-release-lab/actions/runs/43097522952) |
| entrypoint | [startup failure](https://github.com/stritphatographir/soup-devops-release-lab/actions/runs/43097526003) | [startup failure](https://github.com/stritphatographir/soup-devops-release-lab/actions/runs/43097529000) |

The [machine-readable snapshot](actions/startup-failures/runs.json) and
[original annotation](actions/startup-failures/annotation.txt) are preserved.
GitHub's status API reported Actions operational when checked, so the precise
root cause remains unknown; a global outage has not been established.

After linting the workflows again, a minimal runner-allocation probe with no
external actions was dispatched, alongside a fresh naive retry:
[service probe](https://github.com/stritphatographir/soup-devops-release-lab/actions/runs/43098327368),
[naive retry](https://github.com/stritphatographir/soup-devops-release-lab/actions/runs/43098330313),
[fixed push check](https://github.com/stritphatographir/soup-devops-release-lab/actions/runs/43098326734).
The naive retry later passed. The service probe returned another startup
failure. The obsolete fixed push check continued to report queued through the
GET API, while a cancellation request was rejected as already completed; the
same inconsistency affected the first fixed push. Those unsuccessful cleanup
requests are recorded in [this snapshot](actions/obsolete-queued-runs.json), and
are not counted as validation. The fresh fixed run and all fault pairs above
have complete job logs and independently verified outcomes.

## Account configuration and reviewers

The GitHub `testpypi` environment was created and its deployment policy was
verified through the API: custom tag rule `v*`, no branch rule. No TestPyPI
publisher registration, OIDC upload, or public read-back has been confirmed;
the account owner must finish the pending-publisher setup in
[PUBLISHING.md](../docs/PUBLISHING.md) before the first release tag.

[Antigravity's review](../docs/reviews/ANTIGRAVITY.md) completed. Its follow-up
edit task twice ended without a completion report; that exact owned worker was
then stopped with confirmed process termination. The coordinator applied the
budget, cleanup, concurrency, and verdict clarifications. The original review
is retained. A fresh retry after reapplying hooks reached an explicit provider
quota error and was stopped with confirmed termination; no subscription or
model change was made. [OpenCode's independent pipeline review](../docs/reviews/OPENCODE.md)
completed, and its verifier-fix task completed with an explicit worker report.
The coordinator independently verified the fixes. The coordinator already
closed its Docker artifact-identity and fault/matrix coverage findings; the
55b79e0 hosted fixed run verifies those changes.

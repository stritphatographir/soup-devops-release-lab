# Evidence ledger

Repository: https://github.com/stritphatographir/soup-devops-release-lab

The local logs contain actual exit codes. Deliberately broken fixtures are
never published. **Required hosted red/green acceptance and TestPyPI publication
remain unverified.** A startup failure is an infrastructure failure, not proof
of package-bug detection.

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
No native macOS execution has been observed. The configured 15-environment
Actions matrix must still pass before its compatibility claim is accepted.

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
These were queued at the last inspection; no success is inferred.

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
is retained. OpenCode's independent pipeline review is still running.

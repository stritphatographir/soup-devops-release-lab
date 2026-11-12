# Publishing and evidence collection

Repository: https://github.com/stritphatographir/soup-devops-release-lab

## Completed release

The existing `v0.9.4` tag points to
`9ab7279d35904d85d3b835b4bf95884dd473d4f3`. Its
[release run](https://github.com/stritphatographir/soup-devops-release-lab/actions/runs/43224278803)
passed all 21 jobs, including the 15-leg native consumer matrix, exact-artifact
Docker check, OIDC publication, and public wheel/sdist read-back on Python 3.10.
The [TestPyPI project](https://test.pypi.org/project/soup-release-lab-amirt/0.9.4/)
contains exactly those two tested files. A fresh Windows Python 3.13 Simple
Index wheel consumer also passed after checking its downloaded hash.

`evidence/actions/testpypi-release/` retains the run/log, manifest, public hashes,
Simple Index response, provenance responses and Windows consumer output.
Public provenance identity and digest fields match the expected publisher and
files; no independent cryptographic signature verification is claimed.

The immutable published description is from the tagged README, which predates
this status update. Do not recreate or move the existing tag or replace version
0.9.4 to update its description.

## One-time TestPyPI setup (completed for this repository)

The applicant completed separate TestPyPI account login and email verification.
The following pending publisher was registered through
https://test.pypi.org/manage/account/publishing/ and became the project's
publisher when the first OIDC release succeeded:

| Field | Value |
| --- | --- |
| Project | `soup-release-lab-amirt` |
| GitHub owner | `stritphatographir` |
| Repository | `soup-devops-release-lab` |
| Workflow filename | `release.yml` |
| Environment | `testpypi` |

For a different project, choose an available name and update project metadata,
the bundle guard, publish workflow, docs, and registration together before its
first tag. No username/password or long-lived PyPI API token is stored in this
workflow.

The GitHub environment `testpypi` has deployment limited to version tags
(`v*`, tag rule). Required reviewers are off for this TestPyPI automation demo.
A future production environment should have an independent approval gate until
the trust controls in SECURITY.md are in place.

The authoritative setup instructions are [PyPI pending publishers](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/)
and [using a publisher](https://docs.pypi.org/trusted-publishers/using-a-publisher/).

## Remote incident runs

From an authenticated GitHub CLI (all commands explicitly select the repository):

```powershell
$repo = 'stritphatographir/soup-devops-release-lab'
foreach ($bug in @('python310', 'windows', 'missing-data', 'entrypoint')) {
    gh workflow run naive.yml --repo $repo --ref main -f "bug=$bug"
    gh workflow run ci.yml --repo $repo --ref main -f "bug=$bug"
}
gh workflow run ci.yml --repo $repo --ref main -f bug=fixed
gh run list --repo $repo --limit 30
```

Each naive run must succeed. Each hardened fault run must actually fail, and its
failed consumer log must name the intended defect. There is no
`continue-on-error` and no harness that changes a failed Actions job into a
passing job. An unrelated infrastructure failure is not proof that the bug was
caught. Fixed checks use all 15 Python/OS combinations; fault runs use three
representative combinations to control cost. Keep all failed runs.

The completed release used these commands at the reviewed commit; they are a
record, not instructions to repeat an existing release:

```console
git tag -a v0.9.4 -m "Verified TestPyPI release 0.9.4"
git push origin v0.9.4
```

Never move a tag to conceal a failed run. If publication already succeeded and a
later step fails, inspect the immutable package and the failing evidence before
choosing the next version. Reusing the same version is not a recovery strategy.
Read-back is part of acceptance, not a way to undo publication.

## Consuming the public release

TestPyPI is a separate index and may lack runtime dependencies. The recorded
consumers bootstrap the reviewed runtime lock from canonical PyPI, then fetch
the candidate without dependency resolution from TestPyPI. They check its hash
against the tested manifest before installation. This avoids mixing indexes
with `--extra-index-url`; it does not exhaust every downstream resolver or
dependency combination. Dependency metadata is checked separately so the
bootstrap cannot hide an undeclared runtime dependency.

## Evidence status

See `evidence/README.md` for executed checks and actual Actions URLs. A workflow
file, a local Docker log, and an Actions run are distinct forms of evidence.
OIDC publication and public read-back are now verified by the completed release,
not inferred from configuration. There is no real-PyPI publisher or GPU rental.

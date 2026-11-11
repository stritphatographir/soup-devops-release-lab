# Publishing and evidence collection

Repository: https://github.com/stritphatographir/soup-devops-release-lab

## One-time TestPyPI setup

Create a separate free account at https://test.pypi.org and enable the required
account security settings. At
https://test.pypi.org/manage/account/publishing/ register this pending publisher:

| Field | Value |
| --- | --- |
| Project | `soup-release-lab-amirt` |
| GitHub owner | `stritphatographir` |
| Repository | `soup-devops-release-lab` |
| Workflow filename | `release.yml` |
| Environment | `testpypi` |

If the package name is taken, choose a unique name and update project metadata,
the bundle guard, publish workflow, docs, and registration together before the
first tag. Do not put a username/password or API token in the workflow.

Create the GitHub environment `testpypi` with deployment limited to version tags
(`v*`, tag rule). Leave required reviewers off for this TestPyPI automation demo.
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

Once the publisher is saved and fixed checks pass, tag the reviewed commit:

```console
git tag -a v0.9.4 -m "Verified TestPyPI release 0.9.4"
git push origin v0.9.4
```

Never move a tag to conceal a failed run. If publication already succeeded and a
later step fails, inspect the immutable package and the failing evidence before
choosing the next version. Reusing the same version is not a recovery strategy.
Read-back is part of acceptance, not a way to undo publication.

## Evidence status

See `evidence/README.md` for executed checks and actual Actions URLs. A workflow
file, a local Docker log, and an Actions run are distinct forms of evidence.
Missing account setup remains explicitly unverified until a real OIDC publish
and read-back run has succeeded.


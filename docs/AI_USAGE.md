# How I used AI

I used Codex for implementation and automated checks, and asked for OpenCode
and Antigravity as additional reviewers. AI did substantial engineering work
on this submission. This page separates that work from my own involvement and
links the results used to assess it.

## What I handled

I requested the additional reviews, completed GitHub and TestPyPI account login
and verification, and asked for another hook attempt when a review stalled.
I also questioned the GitHub identity being used and specified
`stritphatographir` as the intended owner and commit account. That led to a
correction of the commit email; the next commit's author, committer, and push
actor were checked through GitHub's API. Published history was preserved.

These are my confirmed direct contributions. The technical implementation and
executions below were carried out by the tools, rather than manually by me.

## What each tool contributed

- **Codex:** produced the CLI, fault fixtures, workflows, test harnesses, and
  documentation; ran local checks; dispatched Actions; configured the TestPyPI
  publisher after my account steps; and checked the public release.
- **OpenCode:** reviewed the pipeline and implemented verifier fixes, including
  tag identity, dependency metadata, and explicit failure handling. Codex then
  reran the tests and incident reproduction.
- **Antigravity:** completed an initial review covering evidence, GPU costs,
  cleanup, and release controls. Its follow-up did not complete; a hook retry
  reached a provider quota error. Codex applied the documented follow-up fixes.

## Multi-agent workflow in Orca

Orca is the app I used to run several coding agents side by side. Work was
split into separate implementation, review and follow-up tasks. I requested
OpenCode and Antigravity alongside Codex; Codex dispatched the tasks,
collected findings and checked follow-up changes against tests and run logs.
So the review loop was agents checking agents, with me setting it up, not
reading the diffs. The [review records and resolution ledger](reviews/RESOLUTIONS.md)
document completed reviews, follow-up fixes and failed attempts.

Where the tools were unreliable: Codex's first dependency pins failed the
audit; one OpenCode concern (artifact-download permissions) did not reproduce
in hosted runs; Antigravity's follow-up stalled and then hit a quota error.

## How suggestions were checked

The recorded local commands were run by Codex; the hosted jobs were run by
GitHub Actions. The evidence includes:

- Four naive green runs and four hardened red runs, with the intended error
  checked inside the required failed consumer's log.
- A fixed 15-environment matrix, Docker checks of the same built artifact,
  and 107 passing tests with 96.15% combined package line/branch coverage.
- [TestPyPI release 0.9.4](https://github.com/stritphatographir/soup-devops-release-lab/actions/runs/43224278803):
  all 21 jobs passed, including OIDC publication and public wheel/sdist
  read-back. Public hashes matched the tested artifact. A separate fresh
  Windows Simple Index wheel consumer also passed.

The accepted changes included installing outside the checkout, testing native
Windows, rebuilding the sdist, checking dependency metadata, and isolating
OIDC permissions to a publisher that uploads the tested bytes. Their actual
outcomes and limits are in the [evidence ledger](../evidence/README.md).
Public provenance identity and digest fields were inspected; independent
cryptographic signature verification was not performed.

## One suggestion that needed correction

The initial familiar build/test pins installed successfully but failed the
current dependency audit: pytest, setuptools, and wheel had reported
advisories. Codex updated the pins, regenerated the locks, and reran the audit.
The [original failed audit](../evidence/local/initial-dependency-audit.txt)
was kept. Early workflow lint also caught an invalid YAML command before
remote execution. These are documented corrections made by the tools, not
claims that I independently found them.

## Personal technical verification

Independent code review, local test execution, and manual code changes by me
have not yet been recorded. I do not count an agent-run check as a check I ran
personally. This section should be updated with specific files, commands, and
observations after my own review.

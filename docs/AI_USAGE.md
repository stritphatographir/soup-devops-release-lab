# How I used AI

AI agents generated the implementation. I reviewed the core parts and remained
involved throughout development. I used Codex for implementation and automated
checks, and requested OpenCode and Antigravity as additional reviewers. This
page separates my confirmed review and involvement from code generation and
recorded test execution.

## What I handled

I requested the additional reviews, completed GitHub and TestPyPI account login
and verification, and asked for another hook attempt when a review stalled.
I also questioned the GitHub identity being used and specified
`stritphatographir` as the intended owner and commit account. That led to a
correction of the commit email; the next commit's author, committer, and push
actor were checked through GitHub's API. Published history was preserved.

Alongside my core review, these account and coordination steps were my direct
involvement. The implementation and historical package/CI executions below remain attributed
to the agents and GitHub Actions. In a subsequent, separate lab experiment, I
personally ran the AI-generated GPU-probe commands and shared their output.
Codex did not connect to the server over SSH.

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
The agents supplied additional review perspectives. The
[review records and resolution ledger](reviews/RESOLUTIONS.md) document
completed reviews, follow-up fixes and failed attempts. Multiple agent reviews
do not establish independent validation of every result.

Where the tools were unreliable: Codex's first dependency pins failed the
audit; one OpenCode concern (artifact-download permissions) did not reproduce
in hosted runs; Antigravity's follow-up stalled and then hit a quota error.

## How suggestions were checked

The historical local package checks were run by Codex; hosted jobs were run by
GitHub Actions. Their evidence includes:

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
then-current dependency audit: pytest, setuptools, and wheel had reported
advisories. Codex updated the pins, regenerated the locks, and reran the audit.
The [original failed audit](../evidence/local/initial-dependency-audit.txt)
was kept. Early workflow lint also caught an invalid YAML command before
remote execution. These are documented corrections made by the tools, not
claims that I independently found them.

## Personal technical verification

**Confirmed:** I reviewed the core parts and remained involved throughout
development. This confirmation was supplied during the current documentation
revision; it is not backdated into earlier review reports or execution logs.

**Subsequent hands-on work:** I executed a separate AI-generated CUDA probe on
my own RTX 5090 lab host: compiled it in a digest-pinned container, observed the
expected no-GPU failure (exit 1), ran a kernel whose 65,536 vector-add results
matched the CPU reference (exit 0), and ran a CPU-only timeout control (exit 124).
The reported container listings were empty afterward, and GPU memory returned
to the reported baseline. [The lab report](GPU_LAB_RESULTS.md) records the exact
scope, source/image hashes, output provenance, and a separate terminal paste
error. Codex supplied the test and checked the output I shared; I ran the SSH
commands myself.

**Not claimed:** authorship of specific components, ownership of every design
decision, personal execution of the historical package/CI checks, debugging
particular package failures, or independent validation of every result. A
tool-run check remains attributed to the tool or GitHub Actions. Personal review
of the Windows failure log and an independent manual check of the public wheel's
hash remain unconfirmed.

The original review reports and evidence retain their historical wording and
timestamps. Their earlier pending-review statements describe what was confirmed
at that point, rather than the current review status.

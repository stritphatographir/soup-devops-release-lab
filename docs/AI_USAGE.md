# AI and tool use disclosure

Codex read the brief, designed and wrote the initial package, fixtures, scripts,
workflows, documentation, and note, executed the recorded local checks, and
created the repository and dispatched the recorded Actions runs. Initial remote
runs failed inside GitHub before any jobs existed; they are not successful check
executions. OIDC publication and the full hosted matrix remain unverified.
The applicant requested OpenCode and Antigravity review as additional tools;
their actual outcomes are recorded in the evidence rather than assumed.
No personal claim that the applicant manually
performed these checks is implied.

Accepted implementation suggestions included testing wheels outside the source
checkout, rebuilding and installing the sdist in a second clean environment,
testing native Windows, isolating OIDC to the publisher, and publishing the same
bytes that were tested. They were checked against executable fixture failures,
the fixed consumers, workflow linting, and the upstream PyPI/GitHub documentation.

One unreliable initial suggestion was using familiar older build/test pins.
The first dependency audit found advisories in pytest, setuptools, and wheel.
Those versions were replaced, locks regenerated, and the audit rerun. The failed
audit is kept in `evidence/local/initial-dependency-audit.txt`. Early workflow
lint also caught an invalid unquoted YAML command; it was corrected before
remote execution. These fixes are work performed by the assistant, not evidence
of an independent human review.

Before submitting, the applicant should read the diff and failed logs, run the
CLI and one fixture personally, and update this disclosure with what they
actually accepted, changed, or redid. Do not mark that review as complete until
it has happened. The brief's live-discussion answers are intentionally not
prewritten.

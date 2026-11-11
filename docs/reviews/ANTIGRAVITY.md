# Antigravity review: GPU design, release gating, verdict honesty

Reviewer: Antigravity (Orca worker, task `task_534c6a8152ce`), 2026-11-12.
Scope: `docs/GPU_CI.md`, `docs/SECURITY.md`, `docs/PUBLISHING.md`,
`docs/AI_USAGE.md`, `docs/REFLECTION.md`, `.github/workflows/release.yml` (and
`checks.yml`, which it calls), checked against the brief
`Soup-Task-03-DevOps-Engineer(1).pdf`.

I only read files and public web sources. I did not start any GPU job, spend
money, touch credentials, publish anything, or trigger or query Actions. **I did
not see the result of any Actions run**, so this review does not assume a queued
or dispatched run passed. This review describes only the documents. It does not
speak to the applicant's personal experience, and it does not draft answers for
the live discussion.

## Summary

| Area | Verdict |
| --- | --- |
| Monthly cost arithmetic | Correct. Price agrees with a third-party summary of the provider page. Assumptions are reasonable, with two gaps (F2, F5) |
| Release / nightly gating | Sound in principle. Two inconsistencies: compatibility-set cost (F2) and a single concurrency group (F3) |
| Cancellation-safe cleanup | Strong: broker TTL, an independent watchdog, an `always()` path, and reconciliation by allocation ID. Small gaps (F4) |
| Untrusted PR exposure | No exposure found, in the design or in the implemented workflows (F7) |
| Implemented vs designed | Clearly separated in the GPU and security docs. Submission-level gaps remain (F1) |
| Unattended real-PyPI verdict | Honest and appropriately negative. A clear "fix first" priority is missing (F6) |

No High-severity defects in the GPU design itself. The most important open
items are about completing the submission and its evidence (F1), not the design.

## Arithmetic check (GPU_CI.md "Cost assumptions")

I recomputed every figure with Python:

| Item | Doc | Recomputed |
| --- | --- | --- |
| Releases: 2 x (20 + 3) | 46 min | 46 min |
| Nightlies: 30 x (10 + 3) | 390 min | 390 min |
| Compute: 436/60 h x $0.89 | $6.47 | $6.4673 |
| Retries: 20% of compute | $1.29 | $1.2935 |
| Total incl. $1.00 logs/fixtures | $8.76 | $8.76 |

Extra checks I ran to see whether the $15 ceiling holds up:

- **Worst case at TTL (no retries):** 2 x 25 + 30 x 15 = 500 min, which is **$7.42**.
- **Worst case at TTL, every run retried once:** 1000 min, which is **$14.83**. That
  is under the $15 ceiling, so the TTLs and the ceiling agree with each other.
- **Cost per allocation:** release $0.34 expected / $0.37 at TTL. Nightly $0.19 / $0.22.
  The broker's "refuse allocations whose max TTL cost exceeds remaining budget"
  rule is therefore workable.
- **Disk:** a 50 GB container disk at $0.10/GB-month for 436 min is about $0.05.
  The $1.00 allowance covers it easily.
- **Startup sensitivity:** with 10 minutes instead of 3 for provisioning and image
  pull, the budget is 660 min, $9.79 compute, or $12.75 including the 20% retry
  allowance and the $1.00 allowance. That is still under $15. However, the
  15-minute nightly TTL would then kill the nightly, so the run fails red rather
  than overspending (F5).

**Price source.** A web search confirmed the cited Runpod Secure Cloud RTX 4090
price of **$0.89/hr, per-second billing** (Community Cloud is about $0.34). The
confirmation came from a search summary that cites runpod.io; I could not open
the pricing page directly. Third-party summaries of Runpod's billing docs say
container disk is not charged after stop, volume disk is charged while stopped,
and pods stop when the prepaid balance reaches $0. Re-check all of this at
provisioning time, as the doc already says.

## Findings

### F1 — Medium — Submission and evidence boundaries are incomplete (not a GPU-design defect)

Evidence:
- `README.md` L17–19 says implementation, evidence, and limitations are
  "documented below as verification is completed". Nothing follows.
- `evidence/README.md` L5–7 has no Actions URLs yet.
- `docs/AI_USAGE.md` L3–7 says Codex "executed the recorded local and GitHub
  checks" and that the reviewers' outcomes "are recorded in the evidence".
  Neither is in the repo yet: there are no run URLs, and `docs/reviews/` did not
  exist before this file.
- The brief requires links to red and green Actions runs, a note of ≤2 pages,
  and a reflection paragraph. I could not identify a single ≤2-page note: the
  content is split across five docs.

Impact: today the docs correctly avoid claiming success. But the AI_USAGE wording
claims more than the ledger shows. Gap: either add the real run URLs (red runs
included) and point to this review file, or soften the AI_USAGE wording. Add or
name the ≤2-page note. Fix the dangling "below" in the README.

### F2 — Medium — The release cost does not cover "the whole supported compatibility set"

Evidence: GPU_CI.md L24–25 says "run the whole supported compatibility set
before release". The cost table (L34) budgets one 20 + 3 minute run per release.

Impact: if the set has N driver/framework combinations, release GPU time grows
roughly N times, or the 20 minutes has to cover all N in sequence. Neither is
stated. With N = 3 sequential pods, release minutes go from 46 to 138, about
+$1.36/month. The total stays under $15, but the table is no longer the actual
plan. Also, on rented pods the host driver is chosen by the provider. In
practice you can only filter hosts by CUDA version, so "rotating drivers" needs
stating as "filtering hosts by supported CUDA version".

Gap: name the compatibility set (or N), and say whether it shares one pod or
uses several. Add that to the table, plus a fallback GPU SKU and its price for
when the 4090 is out of stock. L82 already blocks the release in that case.

### F3 — Medium/Low — A single shared concurrency group can drop a pending release GPU run

Evidence: GPU_CI.md L67 says "Use a single concurrency group; cancel superseded
nightlies." In GitHub Actions concurrency, a group holds at most one running and
one pending job. A newly queued job **cancels the existing pending one**, whatever
`cancel-in-progress` is set to. So a nightly queued behind a running release can
replace a pending release, and the reverse.

Impact: this fails closed: a cancelled release run means no publish. But it is a
confusing red result, and the cancellation is exactly the path F4 relies on.
Gap: use separate `gpu-release` and `gpu-nightly` groups. Release groups should
use `cancel-in-progress: false`. Enforce "at most one live pod" in the broker
ledger, not in GitHub concurrency. Check current GitHub docs for any queueing
option before relying on it.

### F4 — Low — Cleanup design is good; a few failure modes are unspecified

The design already covers what matters most:
- Broker-side TTLs (25 min release, 15 min nightly) instead of runner-side timeouts.
- An independent watchdog that reconciles against the ledger after a cancel or a
  dead runner.
- An `always()` path explicitly called insufficient on its own.
- Reconciliation by unique allocation ID before any retry.
- Testing cancel, timeout after create, and failed destroy before enabling the schedule.

Remaining gaps:
- No watchdog interval is given. Worst-case overrun is TTL plus the interval.
- Nothing alerts if the watchdog itself stops (heartbeat / dead-man alert).
- The doc should state that cleanup means **terminate**, not stop. Stopped pods
  with a volume keep billing. L9 and L74 say "destroy" and "delete", which is right,
  but stop vs terminate is the classic trap.
- Pods in the dedicated provider account that are not in the ledger should also
  be deleted.
- A last-line guard is missing for when the provider API itself is down. A
  limited **prepaid balance with auto-reload off** caps spend at the provider,
  which is stronger than the ledger plus an alert (L42–45).
- The pod uploads results with no credentials (L69–70), so it needs a
  short-lived, single-object upload URL. Not stated.

### F5 — Low — Startup allowance and running the same nightly SHA every night

Evidence: L21 and L35 assume 3 minutes for provisioning plus a digest-pinned
CUDA image. That is optimistic for a cold multi-GB image pull. I could not confirm
from Runpod whether pull time is billed. The table runs 30 nightlies whatever has
changed.

Impact: a cost underestimate is bounded (see the sensitivity check). The bigger
risk is false red nightlies when the 15-minute TTL hits during a slow pull. On
cost:
- A nightly on an unchanged SHA spends about $0.19 for no new information.
- A deterministic failure is re-run every night.

Gap:
- Skip the nightly when HEAD equals the last nightly SHA and its result is known.
- Stop allocating after K consecutive failures on the same SHA, until a human or
  a new commit clears it.
- Measure real cold-start time before setting the TTL.

### F6 — Low — The verdict is honest but has no explicit "fix first"

Evidence: SECURITY.md L47–48 gives the verdict "automate TestPyPI; retain a human
gate for real PyPI". It lists prerequisites (L33–37) and states that OIDC and
attestations do not prove correctness or stop a compromised authorized workflow
(L31–32). PUBLISHING.md L59–62 handles the case where publication succeeded but
read-back failed. These are all honest.

Gaps:
- Brief §5 asks "what to fix first". The prerequisites are listed but not ranked.
- SECURITY.md L45–46 says failed publication or read-back "must stop further
  automated releases". Nothing in `release.yml` implements that, so mark it as a
  manual or operational control, not an implemented one.
- The `testpypi` environment's tag-only deployment rule and the pending-publisher
  registration are account settings. They cannot be verified from the repo, and
  the docs say so.

### F7 — Info — No untrusted PR exposure found

Design (GPU_CI.md L60–70):
- The broker checks issuer, audience, repository, workflow, event, ref, and
  environment. It accepts only release tags and the scheduled default branch.
- The provider credential stays in the broker and never reaches the pod.
- No fork PRs on privileged runners. No reuse of self-hosted runners.
- The test container is non-root, holds no credentials, and has restricted egress.

Implemented workflows:
- `ci.yml` uses `pull_request` and `workflow_dispatch`. There is no
  `pull_request_target` or `workflow_run`.
- `checks.yml` has only `contents: read`, uses no `secrets.*`, and checks out
  with `persist-credentials: false`.
- In `release.yml`, only the `publish` job has `id-token: write`. It runs only on
  `v*` tag pushes after `checks`. It does no checkout, install, or build, and it
  re-verifies hashes, source SHA, and tag before calling the SHA-pinned PyPA
  publisher.

Optional hardening: have the broker also pin the immutable `repository_id` /
`repository_owner_id` and `job_workflow_ref` claims, not just names. Note that
with an environment set, the OIDC `sub` changes to
`repo:<owner>/<repo>:environment:<name>`, so the broker must check `ref`
separately, as L60–61 already lists.

### F8 — Info — Implemented vs designed is clearly marked for GPU

GPU_CI.md L3–5 states the CLI is CPU-only and that the GPU part is a design, not
an implementation or a claim that GPU tests ran. L64 says the broker still has
to be built. SECURITY.md L43 lists GPU execution as outside coverage.
`release.yml` contains no GPU job, which matches. The cost exclusions (L41–42)
leave out the **hosting cost of the broker and watchdog**, which should be
listed or estimated.

## AI-usage and reflection docs

- `AI_USAGE.md` and `REFLECTION.md` are labeled as drafts for the applicant to
  revise. They avoid inventing personal experience and explicitly do not
  prewrite live-discussion answers (AI_USAGE L27–28). That fits the brief. The
  only overstatement is the one noted in F1.
- `REFLECTION.md` is in an impersonal voice. The brief asks for the applicant's
  own paragraph on what surprised them, so this remains the applicant's to write.

## Remaining gaps for the coordinator

1. F1: add real Actions URLs (red and green), name the ≤2-page note, fix the
   README "below" reference, and align AI_USAGE with the ledger.
2. F2: size the compatibility set in the cost table and add a fallback SKU.
3. F3: split the GPU concurrency groups, with the broker enforcing a single pod.
4. F4/F5: add the watchdog interval and heartbeat alert, terminate-not-stop, a
   prepaid hard cap, nightly skip on unchanged SHA, and a failure circuit breaker.
5. F6: rank the prerequisites under "what to fix first", and mark the
   "stop further releases" rule as manual.
6. Not verified by me: any Actions run outcome, the TestPyPI publisher and
   environment settings, and a direct load of the live Runpod pricing page.

# GPU release and nightly test design

This CLI is CPU-only. Renting a GPU would add no application coverage today.
The release/nightly design below is for a future CUDA-backed component and
is not an implemented rental or GPU CI integration. A separate
[applicant-run RTX 5090 lab](GPU_LAB_RESULTS.md) records basic CUDA correctness,
a no-GPU failure control, normal cleanup, and a CPU-only timeout control.
That experiment used an owned lab machine; it does not validate the proposed
RTX 4090 rental cost, framework/model behavior, or cloud watchdog design.

## Placement and test scope

Use one **Runpod Secure Cloud RTX 4090 (24 GB)**, on demand, and destroy the pod
after every job. The provider's pricing page listed **$0.89/GPU-hour** when
checked on 2026-11-12. Inventory, startup time, storage, and the price must be
checked again when provisioning. [Provider pricing](https://www.runpod.io/pricing).

For each release, run after the CPU distribution matrix and before publication.
Install the exact candidate wheel by SHA-256 in a digest-pinned CUDA container.
Run CUDA availability and driver/runtime compatibility checks, a deterministic
small tensor calculation against a CPU reference, representative inference with
fixed small input, numerical tolerance checks, synchronization to expose async
errors, and an explicit VRAM limit. Record GPU model, driver, CUDA, Python,
framework versions, seed, peak VRAM, image digest, wheel digest, and timings.
Allow 20 minutes for tests plus 3 minutes for provisioning and image startup.

Initially support exactly one GPU/software tuple per release: one RTX 4090 host
driver, one CUDA image digest, one framework lock, and Python 3.12. Select and
validate those exact versions before enabling the GPU gate; this design does
not claim any tuple has passed. The cost estimate assumes N = 1. With N tuples,
release minutes become `2 x N x 23`, plus any extra nightly coverage.

Nightly, on the protected default branch, use a ten-minute version of the same
suite plus startup allowance. Record the provider's actual host driver; a pod
cannot freely replace it. Expand the supported set only with a new cost estimate.
Keep small fixtures in a versioned, hash-checked object store. Large downloaded
models, benchmarks, and timing thresholds need separate budgets and baselines.
A single 4090 is not evidence for other architectures, multi-GPU, or 80 GB GPUs.

## Cost assumptions, in USD

| Item | Calculation | Monthly estimate |
| --- | --- | ---: |
| Two releases | 2 x (20 + 3) minutes | 46 minutes |
| Thirty nightly runs | 30 x (10 + 3) minutes | 390 minutes |
| GPU compute | 436 / 60 hours x $0.89 | $6.47 |
| Limited infrastructure retries | 20% of compute | $1.29 |
| Small logs/fixtures allowance | no persistent GPU disk | $1.00 |
| Total | rounded planning budget: $10 | **$8.76** |

The estimate assumes an existing small service hosts the broker and watchdog;
new hosting costs need a separate estimate. It excludes taxes, GitHub private-repo
minutes, large model storage, and substantial egress. Use a $15 monthly GPU
provisioning ceiling enforced by the
broker's own metered ledger and an account alert. Provider billing can lag, so an
alert alone is not a hard spending cap. The broker refuses allocations whose
maximum TTL cost, including a one-minute watchdog allowance, would exceed the
remaining budget. Storage/logs remain a separate $1 allowance. This is not a
provider-enforced hard cap during an API outage. Disable automatic balance
top-ups and verify current provider billing semantics before relying on prepaid
credit as an additional guard. With a ten-minute cold start instead of three,
expected compute plus the retry reserve and $1 allowance rises to $12.75.

## Allocation and cleanup controls

```mermaid
flowchart LR
  A[Protected release or nightly SHA] --> B[CPU gates]
  B --> C[OIDC provisioning broker]
  C --> D[One ephemeral GPU pod]
  D --> E[Hash-verified wheel and tests]
  E --> F[Upload logs and destroy pod]
  C --> G[Independent TTL watchdog]
  G --> F
```

The broker verifies GitHub's OIDC issuer, audience, immutable repository and owner
IDs, workflow identity, event, ref, and environment. It accepts release tags and the scheduled default branch
only. It holds a scoped provider credential in a secret store; that credential
never reaches the pod. GitHub's PyPI publishing identity is not a Runpod login.
This broker is additional infrastructure that must be built and tested.

Reject failing lint, unit, packaging, or CPU consumer checks before allocating.
Use separate release and nightly concurrency groups; only superseded nightlies
are canceled. Give releases a per-tag group or a validated FIFO queue so a
nightly cannot replace a pending release. The broker's ledger enforces one live
pod and prioritizes releases; GitHub concurrency alone is not the allocation
lock. Skip unchanged successful nightly SHAs unless deliberately checking for
external drift. Pause after two deterministic failures on one SHA until a new
commit or explicit maintainer reset. Never run fork PRs
on a privileged GPU runner, and do not reuse a self-hosted runner across jobs.
Use a non-root test container without repository or publish credentials. Allow
egress only for the required artifact and results endpoints where supported.
Results use a short-lived signed URL for one object, not a reusable storage key.

Set a 25-minute release TTL and a 15-minute nightly TTL at the broker. A separate
watchdog runs every minute, reconciles provider resources with the broker ledger,
and terminates expired pods even if Actions is canceled or the runner dies.
Alert when its heartbeat is more than two minutes old. Also reconcile unknown
pods in the dedicated provider account. Terminate rather than merely stop pods:
retained disks may continue billing. Measure real cold-start times before
committing to the TTLs. Cleanup must run in
an `always()` path and on cancellation, but that path alone is insufficient.
Test cancellation, API timeout after creation, and failed destruction before
enabling a schedule. If resource creation is ambiguous, reconcile using a unique
allocation ID before retrying; never blindly create a second pod.

Retry a transient allocation/network failure at most once within the budget.
Do not retry test, numerical, OOM, or compatibility failures into a green result.
Fail the release gate when GPU coverage is required and unavailable. Retain
failed logs and report whether failure happened during allocation, setup, or
the actual test.

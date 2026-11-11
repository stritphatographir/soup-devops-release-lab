# Release threat model and remaining boundaries

The pipeline protects against accidental packaging mistakes and several concrete
artifact and credential paths. It does not establish that reviewed source or
dependencies are benevolent.

| Silent failure | Implemented control | Practical boundary |
| --- | --- | --- |
| Unpinned dependencies | Exact runtime and build requirements; universal transitive locks; `--require-hashes`, canonical HTTPS index, wheels only for bootstrap dependencies | Locks require deliberate review and updates; the version pin alone is not a safety judgment |
| Dependency bytes swapped or dependency confusion | One explicit PyPI index, no `--extra-index-url`, hashes at install, candidate installed with `--no-deps --no-index` | A malicious dependency selected when generating a new lock still has a valid hash; ordinary downstream installers do not automatically use our lock |
| Cache hides a resolver error | Fresh consumer venvs, no restored venv or pip cache, `--no-cache-dir`, `pip check` | Does not exhaust all downstream dependency combinations |
| Stale/wrong artifact | Fresh output directory must not exist, exactly one wheel and sdist, source SHA and metadata in manifest, same-run artifact ID, SHA-256 checked before testing and again before publish | An attacker controlling the build and workflow can forge both bytes and manifest |
| Fork PR reaches a secret | `pull_request`, read-only permissions, no repository secrets or OIDC in checks, checkout credentials not persisted; no `pull_request_target` or privileged `workflow_run` | Repository administrators must maintain workflow and environment protections |
| Tag differs from package | Exact `vMAJOR.MINOR.PATCH` equality with built metadata; installed `--version` checked against metadata too | Tags and repository write access still need protection |
| Mutable action/image dependency | Actions pinned to upstream commit SHAs; Python container base pinned by digest; current dependency audit is a gate | A pin does not prove upstream code is safe, and hosted runner images remain outside our control |

These choices prioritize integrity, credential isolation, and version identity
because a passing source test does not even exercise those boundaries. There are
unit tests that reject changed distribution bytes, a stale commit, unexpected
files, path traversal in the manifest, and mismatched tags.

The wheel and sdist must also declare the exact supported Requires-Python range
and the project's single marked tomli requirement. This closes a gap in the
consumer setup: preinstalling the hash-locked runtime dependency can otherwise
hide a missing Requires-Dist declaration. Filenames, project names and versions
are checked together. Explicitly empty SHA/tag inputs fail; branch checks omit
the optional tag, while tag-triggered workflow steps require the caller's tag
to equal the actual GitHub ref.

`release.yml` publishes only on a tag after all reusable checks finish. Only its
publish job has `id-token: write`. That job downloads the exact tested artifact,
validates it using inline standard-library code, and invokes the SHA-pinned PyPA
publisher. It does not check out source, install dependencies, or rebuild while
holding the publish identity. The publisher uses TestPyPI's OIDC Trusted
Publisher and requests publish attestations. Read-back verifies the downloaded
wheel and sdist hashes and runs both consumers again. A read-back failure is a
failed release run, even though publication has already happened.

The publish job's inline verifier reads wheel/sdist metadata using only the
standard library and rejects wrong identity, dependency policy, hashes, or file
sets with explicit errors. It uses no assertions as security controls. Tests
extract the actual workflow code and execute adversarial bundles with normal
and optimized Python, comparing its verdicts with the consumer verifier.
Two verifier implementations remain; the tests enforce agreement on the
covered attacks. Their narrow metadata policy fails closed on unsupported
requirement spellings and must be deliberately updated when dependencies change.

OIDC removes a stored PyPI API token; it does not stop a compromised authorized
workflow from publishing. Attestations bind origin and bytes, not correctness.
The TestPyPI environment must allow only version tags and be included in the
publisher registration. Before real PyPI, require independent review for source,
lock, and workflow changes; protect the default branch and tag creation; require
account 2FA; verify a fresh maintainer can recover the release process. Those
account and policy properties cannot be proven from this repository alone.

Still outside coverage: malicious initial pins, unknown vulnerabilities, a
compromised build runner or maintainer, system-library/architecture differences,
optional extras, proxies and offline installs, old pip, locale and permissions
combinations, user-specific configs, behavioral regressions beyond the fixtures,
and GPU execution. A universal wheel is not an exhaustive compatibility proof.
The Node runtime used by pyright also comes from the hosted runner image; the
Python lock does not pin that executable.

Operationally, a maintainer must disable the release workflow/environment after
failed publication or read-back and preserve evidence. This circuit breaker is
a manual control; the current workflow does not latch later releases off.
This lab intentionally has no real-PyPI
publisher. The current verdict is **automate TestPyPI; retain a human gate for
real PyPI** until the remote evidence and repository trust controls are verified.

Fix first: (1) obtain successful hosted execution and actual OIDC publish/read-back
evidence; (2) protect source, locks, workflows, and version tags with independent
review and account recovery; (3) implement and test a durable release circuit
breaker, then broaden compatibility/behavioral coverage. Until then, TestPyPI
automation is a demonstration, not approval for unattended real-PyPI release.

References: [GitHub secure use](https://docs.github.com/en/actions/reference/security/secure-use),
[PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/using-a-publisher/),
[attestation scope](https://docs.pypi.org/attestations/).

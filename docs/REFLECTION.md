# Reflection draft

The result that stands out in this project is how easily source tests can give
false confidence: all four broken fixtures passed naive CI, but failed when
the installed CLI was exercised. The dependency audit exposed a second issue:
familiar, pinned tool versions were still vulnerable. The useful lesson is to
check the artifact and the evidence behind a green result. AI helped produce
and review the implementation, but its review alone was not treated as proof;
the submission keeps real failures, corrected runs, and public-package checks.
The remaining concern is that one repository controls both the producer and
its evidence. A compromised maintainer or runner could still produce harmful
bytes with valid provenance, so independent review and protected release
changes remain necessary before unattended real-PyPI publishing.

This is a draft based on recorded project results. Personal observations and
any hands-on checks should be added after my own review; this paragraph does
not claim that I performed the automated checks myself.

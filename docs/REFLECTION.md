# Reflection

I was surprised that the naive checks passed on Linux even though the installed Windows CLI could not start because it imported `pwd`. I was also surprised that the audit flagged pinned pytest (PYSEC-2026-1845), setuptools (PYSEC-2026-3447 and GHSA-xmj3-9gf7-h52w), and wheel (CVE-2026-24049). The pins were corrected and the audit rerun. I’m still concerned that one repository controls both the build and the evidence used to approve it. Hashes identify the bytes that shipped. Deciding whether they should ship still requires independent review.

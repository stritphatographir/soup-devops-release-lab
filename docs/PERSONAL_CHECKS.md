# Personal checks

**Core review confirmed:** I reviewed the core parts and remained involved
throughout development. I also executed the separate
[RTX 5090 lab probe](GPU_LAB_RESULTS.md), with the reported outcomes recorded
there. This does not establish completion of the Windows-log and public-wheel
hash checks below. Their manual results remain unconfirmed; the blank fields
are instructions, not execution evidence.

## A. Windows failure

1. Open the [naive run](https://github.com/stritphatographir/soup-devops-release-lab/actions/runs/43100265599). Open the source-only job and confirm that the editable install and library tests passed.
2. Open the [hardened run](https://github.com/stritphatographir/soup-devops-release-lab/actions/runs/43100269894). In the Windows Python 3.12 consumer, find the installed CLI traceback. Check that the path includes the consumer venv and site-packages and that the exception names pwd.

- What I observed:
- What it establishes:

## B. Public wheel SHA-256

From the repository root, use an empty download directory.

```powershell
python -m pip download soup-release-lab-amirt==0.9.4 --no-deps --index-url https://test.pypi.org/simple/ -d dl
Get-FileHash -Algorithm SHA256 .\dl\soup_release_lab_amirt-0.9.4-py3-none-any.whl
(Get-Content evidence/actions/testpypi-release/manifest.json -Raw | ConvertFrom-Json).files.'soup_release_lab_amirt-0.9.4-py3-none-any.whl'
```

- Observed hash:
- Manifest hash:
- Match (yes/no):
- What it establishes:
- What it does not establish:

## Record only checks actually completed

Record the command or run URL, environment, actual output, and what the result
establishes. Keep a distinction between reading a historical log and executing
a check yourself.

- Update [AI_USAGE.md](AI_USAGE.md#personal-technical-verification) with those specifics.
- Keep the [README](../README.md#how-i-used-ai), [note](NOTE.md#reflection-and-ai-use),
  and [email draft](SUBMISSION_EMAIL.txt) consistent with the confirmed scope.
- If the note changes, regenerate the PDF with `python scripts/render_note.py`
  and verify it remains two pages.
- Keep earlier evidence and review timestamps unchanged.

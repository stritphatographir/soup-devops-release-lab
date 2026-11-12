# Personal checks

**Status: not completed.** These are instructions for future personal checks,
not evidence that I have performed them.

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

## Update after completing the checks

- [README.md, "What I have not done"](../README.md#how-i-used-ai) — replace that paragraph with what you checked and observed.
- [NOTE.md, final AI paragraph](NOTE.md#reflection-and-ai-use) — update the AI paragraph and regenerate the PDF with scripts/render_note.py. Confirm it still has two pages.
- [SUBMISSION_EMAIL.txt, "AI use" paragraph](SUBMISSION_EMAIL.txt) — update the final sentence in the AI paragraph.
- [AI_USAGE.md, Personal technical verification](AI_USAGE.md#personal-technical-verification) — replace the pending paragraph with the evidence you inspected, commands you ran, and observations.

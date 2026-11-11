# Soup release pipeline lab

A Python CLI and a release pipeline that demonstrate why green source tests do
not prove that the distribution a user installs will work. The fixed version is
**0.9.4**. Four isolated fixtures reconstruct a broken **0.9.3** release.

```console
python -m pip install --require-hashes -r requirements/ci.lock
python scripts/build_release.py --out tmp/release
python scripts/smoke_artifact.py --bundle tmp/release --kind wheel
python scripts/smoke_artifact.py --bundle tmp/release --kind sdist
```

The CLI command is `soup-check inspect examples/service.toml`. Python 3.10 through
3.14 on Linux, Windows, and macOS are the tested support contract in Actions.

Implementation, evidence, publishing setup, and limitations are documented below
as verification is completed. No remote execution or publication is implied by
the presence of a workflow file.


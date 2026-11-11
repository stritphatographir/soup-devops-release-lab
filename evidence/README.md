# Evidence ledger

Repository: https://github.com/stritphatographir/soup-devops-release-lab

The local logs contain actual exit codes. Actions URLs and TestPyPI acceptance
will be added only after those operations have really run. Deliberately broken
fixtures are never published.

| Fault | Why naive checks pass | Required hardened failure |
| --- | --- | --- |
| `python310` | Linux 3.12 has `tomllib`; tests only call library helpers | Installed CLI on Python 3.10: missing `tomllib` |
| `windows` | Linux provides `pwd`; tests never load CLI | Native Windows installed CLI: missing `pwd` |
| `missing-data` | The JSON file exists in the source checkout | Installed wheel cannot read `defaults.json` |
| `entrypoint` | Tests call functions; building does not resolve console entry point | Installed `soup-check` points at `missing_main` |

`local/initial-dependency-audit.txt` records an additional real failure: vulnerable
initial tool pins. It is independent of the four intentionally introduced bugs.
Any infrastructure or integration failures encountered during verification will
be retained alongside the later fixed result.

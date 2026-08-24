# Repository Review Gate

Repository Review Gate is a Codex skill that turns repository evidence into
validated findings, plain-language explanations, human-owned decisions, and
verified remediation tasks.

Its defining rule is simple: priority and decision authority are separate. A
critical issue may have a technically obvious repair, while a medium-risk issue
may require a human to choose the product, architecture, security, or legal
policy before Codex changes anything.

The installable package is in [`repository-review-gate/`](repository-review-gate/).
Run the complete local validation with:

```bash
python3 scripts/validate_repository.py
```

## Continuous integration

GitHub Actions uses the same dependency-free validation command for pushes to
`main` and pull requests. The workflow runs the validator on Python 3.11 and
3.13 with read-only repository access:

```yaml
permissions:
  contents: read
```

See [`.github/workflows/repository-review-gate.yml`](.github/workflows/repository-review-gate.yml)
for the complete workflow.

## Core workflow

```text
Detect → Validate → Explain → Prioritize → Route
                                      ├─ Codex-ready work
                                      ├─ Human decision
                                      ├─ Verify first
                                      └─ Human action
                                             ↓
                                      Remediate → Verify → Record
```

## Licence

MIT. See [`LICENSE`](LICENSE).

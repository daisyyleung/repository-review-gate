---
title: Repository Review Gate glossary
status: active
owner: DaisYY Leung
updated: 2026-08-21
source_of_truth: true
supersedes: []
tags: [repository-review-gate, glossary]
---

# Glossary

- **Priority**: urgency or impact: `P0`, `P1`, `P2`, `P3`, or `UNASSESSED`.
- **Action route**: who or what must act next: `AUTO_FIXABLE`,
  `HUMAN_DECISION_REQUIRED`, `VERIFY_FIRST`, `HUMAN_ACTION_REQUIRED`,
  `ADVISORY`, or `NO_ACTION`.
- **AUTO_FIXABLE**: Codex can choose a bounded technical repair after mutation
  is authorized; it is not pre-authorization.
- **Human decision gate**: a fail-closed stop on dependent remediation while a
  human-owned policy, architecture, security, product, compatibility, data,
  legal, or language choice is unresolved.
- **Accidental defence**: a control that happens to block an exploit without
  repairing the designed security boundary.
- **Documentation contract**: a capability or guarantee stated as current in
  authoritative documentation.
- **Dual verification**: proof that the reported problem is gone and legitimate
  behavior still works.

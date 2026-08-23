---
title: Repository Review Gate accepted decisions
status: active
owner: DaisYY Leung
updated: 2026-08-21
source_of_truth: true
supersedes: []
tags: [repository-review-gate, decisions]
---

# Accepted decisions

## 2026-08-21 initial project configuration

- Build one skill named `repository-review-gate`.
- Co-locate source and Obsidian context in the current project root.
- Inherit global agent rules and add project-specific review, validation,
  mirroring, and publication gates.
- Separate priority from action route; use `UNASSESSED` rather than a verify-only
  priority.
- Treat `AUTO_FIXABLE` as technical eligibility after authorization.
- Default unresolved human-owned decisions to fail closed for dependent work.
- Keep review state in the reviewed repository and make runtime state tooling
  read-only.
- Publish the governed project to `daisyyleung/repository-review-gate` as a
  Public MIT repository on `main` after SHA-bound confirmation.
- Conduct no market research and make no external uniqueness claims.

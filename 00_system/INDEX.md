---
title: Repository Review Gate system index
status: active
owner: DaisYY Leung
updated: 2026-08-21
source_of_truth: true
supersedes: []
tags: [repository-review-gate, system, index]
---

# System index

## Purpose

Route agents to the smallest authoritative context for this project. Keep
identity, current state, architecture, terminology, and source locations here;
do not store run logs or historical findings in this folder.

## Retrieval triggers

Read this index after `AGENTS.md` for every project-scoped task. Open only the
documents linked for the current task.

## Canonical inventory

- [Current state](current-state.md) — lifecycle, approved scope, and current
  delivery status.
- [Architecture](architecture.md) — package boundaries, state ownership, and
  external capability handoffs.
- [Glossary](glossary.md) — canonical classification and lifecycle terms.
- [Validation protocol](../20_protocols/validation.md) — required local and
  release checks.
- [Accepted decisions](../30_memory/decisions.md) — approved project choices.
- [Skill inventory](../40_skills/skill-inventory.md) — authoritative package
  path, activation contract, and mirror.
- [Agent roles](../10_agents/roles.md) — implementation and review ownership.
- [Telemetry index](../50_telemetry/INDEX.md) — non-authoritative run evidence.

## Source of truth

The installable implementation is `../repository-review-gate/`. Repository
tests live in `../tests/`, and the release validator lives at
`../scripts/validate_repository.py`.

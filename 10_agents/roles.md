---
title: Repository Review Gate agent roles
status: active
owner: DaisYY Leung
updated: 2026-08-21
source_of_truth: true
supersedes: []
tags: [repository-review-gate, agents]
---

# Agent roles

- Root agent: owns intake, authority, project integration, validation, user
  communication, mirroring, and GitHub release gates.
- Sol planner: owns high-impact capability boundaries and architectural
  adjudication when required; read-only by default.
- Luna worker: owns approved bounded implementation and tests with exact file
  ownership.
- Terra reviewer: owns independent review or forward-test evidence when the
  risk and task size justify it.

The global delegation protocol remains authoritative.

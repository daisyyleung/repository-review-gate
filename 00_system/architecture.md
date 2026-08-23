---
title: Repository Review Gate architecture
status: active
owner: DaisYY Leung
updated: 2026-08-21
source_of_truth: true
supersedes: []
tags: [repository-review-gate, architecture]
---

# Architecture

The project contains one installable skill. Its dominant responsibility is the
judgment and routing layer between repository evidence and authorized work.

```text
Repository and scanner evidence
        ↓
Validate → Explain → Priority + Action Route
        ↓
Human Decision Gate
        ↓
Decision-complete task or verification plan
        ↓
Authorized remediation → dual verification → durable state
```

Repository tools and dedicated scanners own evidence acquisition. The skill
owns normalization, validation, explanation, classification, gating, and
handoff contracts. Dedicated security skills own exhaustive security discovery;
cleanliness skills own hygiene; implementation skills own approved code changes;
safe GitHub skills own publication and collaboration actions.

Review history belongs to the reviewed repository under `.repo-review/`, never
inside this skill package. The runtime helper may validate and compare that
state but may not create, migrate, overwrite, delete, commit, or publish it.

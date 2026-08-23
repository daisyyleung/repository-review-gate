---
title: Repository Review Gate validation protocol
status: active
owner: DaisYY Leung
updated: 2026-08-21
source_of_truth: true
supersedes: []
tags: [repository-review-gate, validation]
---

# Validation protocol

After the last source change:

1. Run `python3 scripts/validate_repository.py`.
2. Confirm Skill Creator validation passes.
3. Confirm the state helper and its tests run without creating cache or fixture
   mutations.
4. Forward-test the skill with raw fixtures in a fresh agent context.
5. Mirror the complete skill package and compare it recursively byte-for-byte.
6. Run the execute-end-to-end project preflight.
7. Before publication, run the safe GitHub payload and full-history guard.
8. Bind the final push preview and user approval to the exact commit SHA.

Do not describe source checks as runtime verification, or a dirty/unborn tree
as a stable release binding.

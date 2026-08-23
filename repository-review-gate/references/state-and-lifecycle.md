# State and lifecycle

Review state is owned by the reviewed repository, normally under
`.repo-review/`. It is durable, append-preserving evidence—not a cache inside
the skill package. The package helper only reads explicit paths and emits a
deterministic validation or comparison result.

## Contents

- [Ownership and files](#ownership-and-files)
- [Finding lifecycle](#finding-lifecycle)
- [Decision lifecycle](#decision-lifecycle)
- [Verification lifecycle](#verification-lifecycle)
- [Validation](#validation)
- [Comparison](#comparison)
- [Read-only guarantees](#read-only-guarantees)

## Ownership and files

Use exactly these files for a state set:

```text
.repo-review/
├── manifest.json
├── reviews.json
├── findings.json
├── decisions.json
└── verifications.json
```

The manifest binds all records to a repository identity, revision, and review
ID. `reviews.json` records the scope and links. Findings, decisions, and
verifications are separate so a priority change cannot silently become a human
approval and a passed test cannot silently close a finding. See
[artifact contracts](artifact-contracts.md) for field requirements.

Do not add a second database, write state into the installable skill, or use a
generated report as the authority. Git history supplies timestamp, author,
revision, and append-preserving diff when the owner chooses to commit it; the
helper itself never commits or pushes.

## Finding lifecycle

The normal sequence is:

```text
DETECTED → VALIDATED → CLASSIFIED
                         ├─→ WAITING_FOR_HUMAN → APPROVED
                         ├─→ VERIFY_PENDING
                         ├─→ READY_TO_FIX → FIXED → VERIFIED → CLOSED
                         └─→ CLOSED (NO_ACTION or accepted disposition)
```

Allowed transitions are:

- `DETECTED` → `VALIDATED`, `CLOSED`;
- `VALIDATED` → `CLASSIFIED`, `CLOSED`;
- `CLASSIFIED` → `WAITING_FOR_HUMAN`, `VERIFY_PENDING`, `READY_TO_FIX`,
  `CLOSED`;
- `WAITING_FOR_HUMAN` → `APPROVED`, `DEFERRED`, `CLOSED`;
- `APPROVED` → `READY_TO_FIX`, `WAITING_FOR_HUMAN`, `DEFERRED`;
- `VERIFY_PENDING` → `VALIDATED`, `CLASSIFIED`, `CLOSED`;
- `READY_TO_FIX` → `FIXED`, `DEFERRED`;
- `FIXED` → `VERIFIED`, `READY_TO_FIX`;
- `VERIFIED` → `CLOSED`, `REOPENED`;
- `DEFERRED` → `WAITING_FOR_HUMAN`, `READY_TO_FIX`, `REOPENED`, `CLOSED`;
- `CLOSED` → `REOPENED`;
- `REOPENED` → `VALIDATED`, `CLASSIFIED`, `WAITING_FOR_HUMAN`,
  `VERIFY_PENDING`.

The helper checks `previous_status` when supplied and checks every adjacent
entry in an optional `status_history` list. A new record without history is
valid at any known status, but a claimed transition must be legal. Keep a
closure reason and verification link when closing.

## Decision lifecycle

Decision statuses are `OPEN`, `APPROVED`, `DEFERRED`, `REJECTED`, `SUPERSEDED`,
and `REOPENED`. Typical transitions are:

```text
OPEN → APPROVED | DEFERRED | REJECTED
APPROVED → REOPENED | SUPERSEDED
DEFERRED → OPEN | APPROVED | REJECTED
REJECTED → REOPENED | SUPERSEDED
REOPENED → OPEN | APPROVED | REJECTED
```

`SUPERSEDED` is terminal for that record and must link to a successor when one
exists. A new decision does not erase the prior rationale. Approval requires a
chosen option, rationale, approver, and repository revision. Policy approval
does not grant mutation authorisation; record the latter in the bounded task or
owner workflow.

## Verification lifecycle

Verification statuses are `PENDING`, `PASSED`, `FAILED`, `BLOCKED`, and
`SUPERSEDED`. Typical transitions are:

```text
PENDING → PASSED | FAILED | BLOCKED | SUPERSEDED
BLOCKED → PENDING | SUPERSEDED
FAILED → PENDING | SUPERSEDED
PASSED → SUPERSEDED
```

`PASSED` and `FAILED` require evidence with source, revision, scope, and detail.
A passed verification must prove both that the original failure is gone and
that the legitimate path still works. If it proves only implementation text,
label the quality degraded and keep runtime verification pending.

## Validation

Run the helper with an explicit path:

```text
python3 repository-review-gate/scripts/review_state.py validate /repo/.repo-review
```

Validation checks UTF-8 JSON, top-level schema version, required files and
arrays, ID syntax and uniqueness, manifest review/repository identity,
referential integrity, dependencies, decision dependencies, evidence
provenance, enums, approval completeness, and supplied transitions. Use
`--repository-id` to assert the expected identity; this catches state copied
from a different repository. A nonzero exit means no result may be treated as
authoritative.

The helper does not infer missing fields, migrate old versions, repair IDs, or
rewrite paths. Fix state through the owner-approved workflow and rerun
validation.

## Comparison

Compare two explicit state paths:

```text
python3 repository-review-gate/scripts/review_state.py diff /repo/old/.repo-review /repo/new/.repo-review
```

The result sorts IDs and reports:

- `new_findings`: IDs absent before and present now;
- `resolved_findings`: previously active IDs now `CLOSED`;
- `reopened_findings`: previously `CLOSED` IDs now active or explicitly
  `REOPENED`;
- `decision_deltas`: stable decision IDs whose status or chosen decision changed,
  plus sorted `new`, `approved`, `reopened`, `deferred`, `rejected`, and
  `superseded` sets;
- `changed_findings`: existing IDs whose priority, canonical action route, or
  status changed. Renaming the legacy `ownership` field to `action_route`
  without changing its value is not a semantic change.

For integrations that use the shorter vocabulary, `new`, `resolved`, and
`reopened` are deterministic aliases of the corresponding finding-prefixed
arrays.

The comparison is deterministic for the same JSON content and does not use
timestamps or file order. It does not decide whether a new finding is real,
whether a decision is wise, or whether a mutation is authorised.

## Read-only guarantees

The helper opens files in read mode, never creates directories, never writes
JSON, and never calls Git, network, deployment, or external services. Tests
should snapshot state and raw fixtures before and after both subcommands and
assert byte identity. Use `PYTHONDONTWRITEBYTECODE=1` during validation so no
cache artefacts are left beside the helper.

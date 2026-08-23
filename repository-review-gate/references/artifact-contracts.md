# Artifact contracts

These contracts describe the JSON files stored in the reviewed repository's
`.repo-review/` directory. They are intentionally scanner-agnostic. The
read-only helper validates the structural and referential rules; prose reports
may render the same records but must not silently alter them.

## Contents

- [Common rules](#common-rules)
- [Manifest](#manifestjson)
- [Reviews](#reviewsjson)
- [Findings](#findingsjson)
- [Decisions](#decisionsjson)
- [Verifications](#verificationsjson)
- [Evidence and handoff fields](#evidence-and-handoff-fields)

## Common rules

Every file is a UTF-8 JSON object with:

```json
{"schema_version": 1}
```

The top-level `schema_version` is the integer `1`. Files are append-preserving
records: update an item by stable ID and retain its history or previous review
entry. IDs are unique across all five files and use a readable prefix such as
`REVIEW-001`, `F-001`, `DECISION-001`, or `VERIFY-001`. IDs are case-sensitive,
non-empty, and contain only letters, digits, `.`, `_`, `:`, or `-`.

The required state files are exactly:

```text
manifest.json
reviews.json
findings.json
decisions.json
verifications.json
```

Unknown top-level keys are preserved by the helper, but required arrays and
objects must have the documented types. Unknown item fields are allowed so a
scanner can retain provenance; reserved fields must keep their meaning.

## `manifest.json`

The manifest binds the state to a repository and review sequence:

```json
{
  "schema_version": 1,
  "repository": {
    "id": "public-example",
    "root": "/workspace/public-example",
    "revision": "abc123"
  },
  "review_id": "REVIEW-001",
  "created_at": "2026-08-21T00:00:00Z",
  "updated_at": "2026-08-21T00:00:00Z",
  "status": "COMPLETE"
}
```

`repository.id`, `repository.root`, and `repository.revision` are required
non-empty strings. The helper treats `repository.id` as the identity key and
checks optional `repository_id` fields in other files or items against it.
`root` is descriptive state, not a path the helper may create or inspect.
`review_id` must be present in `reviews.json`. `status` is `RUNNING`,
`COMPLETE`, `FAILED`, or `ABORTED`.

## `reviews.json`

The review list records scope and stable links:

```json
{
  "schema_version": 1,
  "reviews": [
    {
      "id": "REVIEW-001",
      "repository_id": "public-example",
      "revision": "abc123",
      "scope": ["correctness", "architecture"],
      "status": "COMPLETE",
      "finding_ids": ["F-001"],
      "decision_ids": ["DECISION-001"],
      "verification_ids": ["VERIFY-001"],
      "started_at": "2026-08-21T00:00:00Z",
      "completed_at": "2026-08-21T00:10:00Z"
    }
  ]
}
```

`id`, `repository_id`, `revision`, and `status` are required. The three ID
arrays are optional but, when present, must resolve. The manifest's
`review_id` must identify one review in this array. Keep scope explicit; an
unscoped review must state why its evidence is sufficient.

## `findings.json`

Findings carry independent priority and route:

```json
{
  "schema_version": 1,
  "findings": [
    {
      "id": "F-001",
      "repository_id": "public-example",
      "review_id": "REVIEW-001",
      "title": "Success response renders the error state",
      "category": "correctness",
      "priority": "P1",
      "confidence": "HIGH",
      "status": "CLASSIFIED",
      "files": ["src/forms/signup.ts"],
      "lines": [42, 47],
      "evidence": [{
        "source": "src/forms/signup.ts",
        "revision": "abc123",
        "scope": "signup submit handler",
        "detail": "success branch assigns error banner"
      }],
      "root_cause": "The success branch calls the error renderer.",
      "user_impact": "A successful signup looks failed.",
      "plain_language_explanation": "The account works, but the screen says it did not.",
      "action_route": "AUTO_FIXABLE",
      "proposed_fix": "Render the success state and add a behavioural regression test.",
      "decision_dependency": null,
      "dependencies": [],
      "acceptance_criteria": ["Success shows confirmation", "Failure still shows an error"],
      "verification_method": "Run the form behaviour test and inspect both responses"
    }
  ]
}
```

Required finding fields are `id`, `title`, `category`, `priority`, `confidence`,
`status`, `action_route` (or the backwards-compatible `ownership` alias),
`evidence`, `acceptance_criteria`, and `verification_method`. `files`, `lines`, explanations, and proposed work are
strongly recommended; a missing one should be called out in the report.
`decision_dependency` may be `null`, one decision ID, or a list of decision IDs.
`dependencies` may list finding IDs. All references must resolve.

`confidence` is `LOW`, `MEDIUM`, or `HIGH`. `category` is a non-empty lower-case
label such as `correctness`, `security`, `architecture`, `testing`, `docs`,
`ux`, `pilot`, `legal`, or `cleanliness`; the helper does not restrict future
categories. Priority and action route use the enums in
[classification and gates](classification-and-gates.md).

## `decisions.json`

Decision records hold the human-owned choice independently from a finding:

```json
{
  "schema_version": 1,
  "decisions": [
    {
      "id": "DECISION-001",
      "repository_id": "public-example",
      "review_id": "REVIEW-001",
      "title": "Choose the authoritative state layer",
      "problem": "DB and TypeScript enforce different transitions.",
      "why_ai_cannot_decide": "Changing authority changes the architecture contract.",
      "recommended_option": "database",
      "options": ["database", "typescript", "documented hybrid"],
      "tradeoffs": ["Database centralises invariants", "Application is easier to iterate"],
      "affected_findings": ["F-002"],
      "status": "OPEN",
      "decision": null,
      "rationale": null,
      "approved_by": null,
      "approved_at_revision": null
    }
  ]
}
```

Required fields are `id`, `title`, `problem`, `why_ai_cannot_decide`,
`recommended_option`, `options`, `tradeoffs`, `affected_findings`, and `status`.
The recommendation and an approved decision must name an option in `options`.
A decision is required when status is `APPROVED`; `decision`, `rationale`, `approved_by`,
and `approved_at_revision` must then be non-empty. Status may be `OPEN`,
`APPROVED`, `DEFERRED`, `REJECTED`, `SUPERSEDED`, or `REOPENED`.

## `verifications.json`

Verification records bind proof to a finding:

```json
{
  "schema_version": 1,
  "verifications": [
    {
      "id": "VERIFY-001",
      "repository_id": "public-example",
      "review_id": "REVIEW-001",
      "finding_id": "F-001",
      "method": "Run behaviour test with success and failure responses",
      "status": "PASSED",
      "evidence": [{
        "source": "tests/signup.test.ts",
        "revision": "def456",
        "scope": "success and failure cases",
        "detail": "both assertions pass"
      }],
      "verified_at_revision": "def456"
    }
  ]
}
```

Required fields are `id`, `finding_id`, `method`, and `status`. Status is
`PENDING`, `PASSED`, `FAILED`, `BLOCKED`, or `SUPERSEDED`. `evidence` is
required when status is `PASSED` or `FAILED`; each item must record source,
revision, scope, and detail. A passed verification does not itself close a
finding; the finding status must be updated with the resulting evidence.

## Evidence and handoff fields

Every evidence item has these non-empty strings:

```json
{
  "source": "path/or/report-id",
  "revision": "immutable-revision",
  "scope": "what was examined",
  "detail": "what was observed"
}
```

Use `source_kind` (`repository`, `scanner`, `runtime`, `human`, or another
explicit label) when useful. Do not put secrets or private repository content
in `detail`. Handoff records should include finding and decision IDs, exact
files/symbols, non-goals, acceptance criteria, test level, mutation scope,
rollback notes, and post-change verification evidence. A report may link to
these fields; it must not invent an approval or a revision that is absent from
the record.

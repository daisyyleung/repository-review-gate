# Classification and gates

This is the canonical vocabulary for separating impact from decision ownership.
The same finding may be P0 and `HUMAN_DECISION_REQUIRED`, or P3 and
`VERIFY_FIRST`; never derive one field from the other.

## Contents

- [Priority](#priority)
- [Action routes](#action-routes)
- [Decision gate](#decision-gate)
- [Safety matrix](#safety-matrix)
- [Decision record](#decision-record)

## Priority

Use exactly one value:

| Value | Meaning | Typical response |
| --- | --- | --- |
| `P0` | Active critical exposure, destructive corruption, or outage needing immediate containment | Contain only with authorised emergency action; escalate owner |
| `P1` | Must fix before pilot or production | Schedule a bounded fix after required gates |
| `P2` | Important risk that does not block current use | Plan and track; do not disguise as a blocker |
| `P3` | Non-blocking improvement, maintainability, or polish | Advisory backlog |
| `UNASSESSED` | Impact cannot yet be established from recorded evidence | Run verification or request human assessment |

`UNASSESSED` is not a synonym for “verify-only” and is not a permanent
priority. When evidence is sufficient, update the priority while preserving the
reason and revision that changed it. Do not use the retired `V` priority.

## Action routes

Use exactly one value:

### `AUTO_FIXABLE`

The change is narrow, technically determinate, reversible, and has no unresolved
architecture, policy, product, compatibility, data, legal, language, security
boundary, destructive, or external-action choice. It means technical eligibility
only. Obtain explicit mutation authorisation before editing, then test both the
failure and the legitimate path.

### `HUMAN_DECISION_REQUIRED`

The implementation can be performed by an agent after a human chooses among
valid directions. Examples include database versus application authority,
fail-open versus fail-closed policy, provider or residency choice, public API
compatibility, retention/deletion semantics, workflow/status changes, and
language/register or legal wording. Stop all dependent implementation until the
item-scoped decision is approved.

### `VERIFY_FIRST`

The claim depends on runtime, deployed bundle, browser, external API, migration
execution, vendor configuration, or another fact not proven by repository
evidence. Write a verification method, expected observation, owner, and
conversion rule. A pass closes or downgrades the item; a failure becomes a
validated finding with a new classification. Do not patch speculatively.

### `HUMAN_ACTION_REQUIRED`

Codex cannot complete the necessary action: legal approval, credential or vendor
console setup, deployment permission, a product owner sign-off, or an external
configuration. State what an agent can prepare and what the owner must do.

### `ADVISORY`

No concrete defect or release risk is proven, but a recommendation may improve
maintainability, usability, or future hardening. It must not block a release or
be represented as a bug.

### `NO_ACTION`

The evidence shows a false positive, obsolete path, intentionally designed
behaviour, or an already-satisfied contract. Include the evidence, revision,
scope, and rationale so the result is auditable and can be reopened if the
assumption changes.

## Decision gate

The gate is item-scoped. A human gate on one finding does not authorise a
related finding unless the decision record names it. Policy approval and
mutation authorisation are distinct:

1. **Policy/design approval:** the owner chooses the direction and records
   rationale, trade-offs, approver, and approved revision.
2. **Mutation authorisation:** the owner permits a bounded edit, migration,
   deletion, external configuration, or publication in the stated scope.
3. **Implementation and verification:** the assigned agent changes only the
   authorised scope and proves both regression and intended behaviour.

Fail closed for unresolved:

- architecture or source-of-truth conflicts;
- authentication, authorisation, tenant, trust-boundary, or security policy;
- product workflow, status, navigation, or pilot contract;
- public API, schema, dependency, provider, or compatibility choices;
- data retention, deletion, cascade, or semantic changes;
- legal, compliance, consent, privacy, or language/register decisions;
- destructive, irreversible, external, credential, deployment, or publication
  actions.

An agent may recommend one option, but the record must label it
“recommendation—not approved”. Never infer approval from silence, a green test,
an earlier unrelated decision, or technical ease.

## Safety matrix

| Evidence or requested change | Default route | Required proof or gate |
| --- | --- | --- |
| Deterministic UI/event bug with a focused regression test | `AUTO_FIXABLE` | Mutation authorisation; behavioural test |
| Dead code with proven no callers, migration use, or public compatibility | `AUTO_FIXABLE` | Reachability evidence; deletion authorisation |
| Competing state or auth authorities | `HUMAN_DECISION_REQUIRED` | Authority decision before refactor |
| Potential missing production dependency | `VERIFY_FIRST` | Build/deploy or bundle inspection |
| Accidental secondary security defence | `HUMAN_DECISION_REQUIRED` or `P0`/`P1` based on impact | Designed boundary decision; exploit/regression proof |
| Source grep standing in for executable behaviour | `ADVISORY` or `P2` based on claim | Behavioural/boundary test plan |
| Consent, terms, privacy, or language mismatch | `HUMAN_ACTION_REQUIRED` or `HUMAN_DECISION_REQUIRED` | Owner/legal/product approval |
| Deleted route reported as live | `NO_ACTION` | Current revision path evidence |

Severity never grants autonomy. A critical but deterministic patch still needs
authorisation; a low-impact architecture conflict still needs a decision.

## Decision record

Use a stable `DECISION-*` ID and include:

- question and problem statement;
- why an AI agent cannot choose safely;
- recommendation and explicit alternatives;
- trade-offs and affected finding IDs;
- requested approval and mutation scope;
- status (`OPEN`, `APPROVED`, `DEFERRED`, `REJECTED`, `SUPERSEDED`, or
  `REOPENED`);
- chosen option, rationale, approver, and approved repository revision;
- successor or superseded decision IDs when the decision changes.

An approved decision is evidence for future regression checks, not a permanent
rule. If implementation contradicts an approved decision, report an
architecture regression against its ID instead of asking the same question
again. If the owner reopens it, preserve the prior record and require a new
decision before dependent changes.

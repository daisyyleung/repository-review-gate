---
name: repository-review-gate
description: Review a repository or imported scanner findings when the task asks for repository-wide correctness, security-boundary, architecture, documentation-contract, testing-quality, pilot-readiness, accessibility, dead-code, language, legal, or product-risk review. Use it to validate evidence, explain technical and user impact, classify priority independently from action ownership, surface human decisions, create bounded remediation and verification work, compare a prior review, or detect regressions against approved decisions. Keep dedicated security discovery, repository cleanliness, implementation, deployment, and GitHub lifecycle actions with their specialised skills; do not invoke this skill for a generic code edit, exhaustive security scan, cleanup-only pass, or publication action.
---

# Repository Review Gate

Use this skill as the judgment and routing layer between repository evidence and
authorised work. It is scanner-agnostic: inspect the repository directly or
normalise reports from linters, tests, accessibility tools, security scanners,
the cleanliness skill, or a human reviewer. Default to review-only. A repair
that appears technically safe is not permission to mutate the repository.

## Contents

- [Operating contract](#operating-contract)
- [Workflow](#workflow)
- [Finding and decision rules](#finding-and-decision-rules)
- [Bounded work and verification](#bounded-work-and-verification)
- [State and repeat reviews](#state-and-repeat-reviews)
- [Handoffs](#handoffs)
- [References](#references)

## Operating contract

1. Record the repository identity, revision, review scope, and evidence source
   before treating a claim as authoritative. Read the repository's `AGENTS.md`,
   README, security and architecture documents, package/deployment files, and
   relevant tests before drawing conclusions.
2. Preserve the sequence **detect, validate, explain, classify, gate, generate,
   verify, record**. Never skip validation because a scanner is confident.
3. Keep priority and action route independent. Priority describes consequence
   and urgency; action route describes who may decide or act.
4. Fail closed when authority, security policy, product behaviour, compatibility,
   data semantics, legal/compliance, language/brand, destructive data, or an
   irreversible external action is unresolved. Present a recommendation and
   alternatives, but do not treat a recommendation as approval.
5. Treat accidental protection as evidence of a broken designed boundary, not as
   proof that a security finding is safe. Treat a source grep as a contract
   assertion, not as runtime proof when behaviour can be exercised.
6. Keep review state in the reviewed repository under `.repo-review/`. The
   bundled helper is read-only and may validate or compare explicit state paths;
   it must never create, migrate, overwrite, delete, commit, or publish state.

## Workflow

### 1. Preflight and history

Confirm the requested scope, repository root, current revision, language, and
available tools. Load the previous `.repo-review/` state when present. On a
first review, establish a baseline; on later reviews, compare the baseline and
still perform a focused full-risk pass so a previously unknown issue is not
missed. If the source revision or scope is absent, mark the evidence
unresolved rather than guessing.

### 2. Map authority and contracts

Make a short authority map for authentication, tenant isolation, state
transitions, persistence, provider/configuration routing, public API contracts,
and documentation claims. Identify competing implementations and approved
decisions before proposing deletion or consolidation. Claims in README,
`AGENTS.md`, security, architecture, deployment, accessibility, privacy, or
provider documentation are release contracts to test against implementation;
do not dismiss a contradiction as cosmetic.

### 3. Acquire and validate evidence

For each candidate, capture source paths, line ranges or stable symbols,
revision, scope, and the observation. Reproduce the affected behaviour when
possible. Distinguish direct evidence, inference, and unknown runtime facts.
Reject stale paths, duplicate reports, speculative fixes, and findings whose
claimed behaviour is not supported by the recorded revision. When external or
deployed behaviour is required, create a verification task instead of changing
code speculatively.

### 4. Explain before classifying

Write both a technical explanation and a plain-language explanation. State the
root cause, affected behaviour, user or operator impact, current danger (yes,
no, or unknown), and what evidence would change the conclusion. For every
finding include a bounded proposed fix, acceptance criteria, and a verification
method. Keep a false positive as `NO_ACTION` with evidence and rationale.

### 5. Classify two independent dimensions

Choose exactly one priority and one action route from the canonical enums in
[classification and gates](references/classification-and-gates.md). A critical
finding may still require a human decision; a low-priority item may still need
runtime verification. Do not use the old `V` priority: uncertainty is the
`VERIFY_FIRST` action route.

### 6. Apply the item-scoped human gate

Stop dependent remediation when an item is architecture-, policy-, product-,
compatibility-, data-, legal-, language-, security-boundary-, destructive-, or
irreversible-action dependent. Create a decision item with the question,
recommendation, alternatives, trade-offs, affected findings, and the exact
approval needed. Policy approval and mutation authorization are separate gates:
approval of a design does not authorise a write, migration, deletion, external
configuration change, or publication.

### 7. Generate bounded work

Only generate a Codex-ready implementation task when the finding is
decision-complete and the mutation is authorised. One task should address one
finding or a tightly coupled acceptance set. Include files in scope, explicit
non-goals, test level, rollback or compatibility notes, and the decision ID when
applicable. Never delete “unused” code without proving reachability, migration,
compatibility, and external-caller assumptions.

### 8. Verify and record

Require two proofs after an authorised fix: the original failure no longer
occurs, and the legitimate path still works. Prefer behavioural, boundary,
integration, or end-to-end tests over source assertions. If only a source-level
test is feasible, label the result `Verification quality degraded` and state
the missing runtime proof. Record findings, decisions, verification evidence,
and append-preserving history in `.repo-review/`; compare by stable IDs on the
next review.

## Finding and decision rules

### Coverage prompts

Use the prompts that fit the requested scope; do not claim exhaustive security
discovery unless the dedicated security skill owns that work.

- **Correctness:** state transitions, persistence, defaults, redirects,
  counters, time zones, forms, races, transactions, and error paths.
- **Security and trust:** authentication, authorisation, tenant isolation,
  RLS or service-role boundaries, SSRF, secrets, OAuth, privilege drift, and
  fail-open defaults. Ingest dedicated scanner evidence rather than duplicating
  its exhaustive search.
- **Architecture:** source-of-truth conflicts, duplicate invariants, stale
  routes, dead abstractions, and incompatible security or data models.
- **Documentation contracts:** compare stated capabilities and guarantees with
  runtime behaviour, configuration, deployment, privacy, accessibility, and
  provider choices.
- **Testing quality:** rate evidence from presence/source checks through
  structural, behavioural, boundary, and real integration coverage. A green
  command does not prove an unexercised claim.
- **Pilot readiness:** failure visibility, operator visibility, honest data,
  recovery, accessibility, critical navigation, and non-silent logging.
- **Explainability and language/legal consistency:** identify unexplained code,
  register mismatch, consent comprehension risk, or legal wording questions;
  route the decision to the owner rather than writing policy yourself.

### Priority

Use `P0` for active critical exposure, destructive corruption, or an outage
requiring immediate containment; `P1` for a must-fix blocker before pilot or
production; `P2` for important risk that does not block current use; `P3` for
non-blocking improvement or maintainability. Use `UNASSESSED` only while the
impact evidence is genuinely incomplete; pair it with `VERIFY_FIRST` or a
human route and resolve it after evidence arrives.

### Action route

- `AUTO_FIXABLE`: technically narrow and reversible after mutation
  authorisation. It is never permission.
- `HUMAN_DECISION_REQUIRED`: implementation is possible, but a human must
  choose architecture, policy, product, compatibility, data, language, legal,
  or security-boundary direction first.
- `VERIFY_FIRST`: runtime, deployment, external API, browser, migration, or
  other evidence is missing. Define the method and conversion criteria.
- `HUMAN_ACTION_REQUIRED`: an owner must approve, configure, provide access, or
  perform an external/legal action that Codex cannot complete.
- `ADVISORY`: useful recommendation without a demonstrated defect or release
  block.
- `NO_ACTION`: false positive, obsolete item, or intentionally safe behaviour;
  cite the evidence and preserve the rationale.

### Human decision item

Use an ID such as `DECISION-001`. State what was found, why an AI agent cannot
choose safely, a recommended option labelled **recommendation—not approved**,
alternatives and trade-offs, affected finding IDs, the approval requested, and
the implementation and verification work that follows each option. Record the
decision, rationale, approver, and approved revision. An approved decision may
later be reopened or superseded; keep the old record and explain the change.

## Bounded work and verification

An implementation handoff must contain: finding and decision IDs; exact files
and symbols in scope; behaviour to preserve; non-goals; acceptance criteria;
test command and required test level; migration/rollback considerations; and a
post-change verification plan. Do not weaken security or tests merely to make a
check green. For runtime uncertainty, verification precedes any patch. For
security, legal, architecture, data deletion, public API, provider, or external
configuration changes, obtain the corresponding human gate even if the code
edit itself looks small.

Use the [artifact contracts](references/artifact-contracts.md) when writing
findings, decisions, reviews, or verification records. Use the
[review protocol](references/review-protocol.md) for evidence quality and
test-level decisions. Use [state and lifecycle](references/state-and-lifecycle.md)
when creating or comparing `.repo-review/` state. Use
[composition and handoffs](references/composition-and-handoffs.md) when another
skill owns discovery, implementation, deployment, cleanup, or GitHub actions.

## State and repeat reviews

The state directory contains exactly these machine-readable records:
`manifest.json`, `reviews.json`, `findings.json`, `decisions.json`, and
`verifications.json`. Validate an explicit directory with the read-only helper:

```text
python3 repository-review-gate/scripts/review_state.py validate /path/to/.repo-review
python3 repository-review-gate/scripts/review_state.py diff /path/to/old/.repo-review /path/to/new/.repo-review
```

The helper emits deterministic JSON and exits non-zero for malformed schema,
duplicate or dangling IDs, wrong repository identity, illegal transitions, or
broken references. It never modifies either path. A diff reports sorted new,
resolved, reopened finding IDs and decision status deltas; it does not infer
approval or authorise a mutation.

## Handoffs

Keep boundaries explicit:

- Send exhaustive security discovery to the dedicated security skill; ingest its
  evidence here for validation, explanation, and gating.
- Send hygiene, stale-file, and cleanup discovery to the cleanliness skill;
  route unexplained privileged or behaviour-affecting code back here.
- Send approved code changes and tests to the implementation skill or bounded
  coding task; this skill supplies acceptance and verification requirements.
- Send deployment, credentials, external dashboards, pull requests, commits,
  merges, and publication to the relevant safe lifecycle skill after all gates.

## Completion checklist

Before reporting a review complete, confirm the revision and scope are recorded,
all findings have technical and plain-language explanations, priority and route
are independent, unresolved decisions are queued, runtime unknowns have a
verification method, authorised work has acceptance criteria, and both target
and regression behaviour were verified. Report partial coverage and blockers
explicitly; do not call an unrun test or an unapproved recommendation complete.

## References

Read only the references needed for the current stage:

- [Review protocol](references/review-protocol.md) — preflight, evidence,
  explanation, test quality, and report structure.
- [Classification and gates](references/classification-and-gates.md) — enums,
  independence rules, and human decision conditions.
- [Artifact contracts](references/artifact-contracts.md) — JSON record shapes,
  required fields, and evidence contracts.
- [State and lifecycle](references/state-and-lifecycle.md) — `.repo-review/`
  ownership, transitions, validation, and deterministic comparison.
- [Composition and handoffs](references/composition-and-handoffs.md) — scope
  boundaries and handoff payloads for companion skills.

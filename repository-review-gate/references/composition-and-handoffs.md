# Composition and handoffs

Repository Review Gate is a routing and judgment layer. It composes with
specialised skills and repository tools without absorbing their ownership.
Every handoff is evidence-led, item-scoped, and explicit about what remains
human-owned.

## Contents

- [Ownership boundaries](#ownership-boundaries)
- [Accepted inputs](#accepted-inputs)
- [Handoff payload](#handoff-payload)
- [Companion routes](#companion-routes)
- [Return contract](#return-contract)
- [Anti-patterns](#anti-patterns)

## Ownership boundaries

| Capability | Owning layer | Review Gate responsibility |
| --- | --- | --- |
| Repository/source inspection | Repository tools and review agent | Validate scope and evidence |
| Exhaustive security discovery | Dedicated security skill | Normalise, explain, classify, and gate imported evidence |
| Hygiene and stale-file discovery | Cleanliness skill | Decide whether a hygiene item affects behaviour or trust |
| Implementation and tests | Bounded coding/implementation task | Supply acceptance and verification requirements |
| Deployment, credentials, vendor consoles | Owner or deployment skill | Identify human action and verify returned evidence |
| Git commits, pull requests, merges, publication | Safe GitHub lifecycle skill | Gate payload, authorisation, history, and revision binding |
| Durable review state | Reviewed repository `.repo-review/` | Validate and compare read-only |

Do not duplicate exhaustive scanner work, silently delete code, write legal or
security policy, choose product language, or publish changes. A scanner's
severity is input evidence—not a priority or action route until validated.

## Accepted inputs

The skill may ingest:

- source files, tests, configuration, migrations, and deployment manifests;
- linter, type-checker, test, accessibility, or build reports;
- dedicated security or cleanliness findings;
- runtime logs, browser observations, or deployed bundle inspection;
- a prior `.repo-review/` state set;
- a human review note or product/architecture question.

For each imported item preserve its source/report ID, tool version if known,
repository revision, scope, raw observation, and any confidence supplied by the
producer. Do not trust an imported classification until the repository evidence
and authority map support it.

## Handoff payload

Send a compact machine-readable or Markdown payload containing:

1. repository identity, revision, and requested scope;
2. finding IDs and source report IDs;
3. evidence items with source, revision, scope, and detail;
4. technical and plain-language explanation;
5. independent priority and action route;
6. decision IDs, recommendation, alternatives, and approval status;
7. exact files/symbols in scope and explicit non-goals;
8. acceptance criteria and required test level;
9. verification method, owner, pass/fail conversion rule;
10. mutation, external-action, or publication authorisation state.

Do not hand off a task that still contains an unresolved design choice. Do not
combine unrelated findings merely to reduce task count. A decision item can
block several findings only when it explicitly names them.

## Companion routes

### Security discovery

Ask the dedicated security skill for exhaustive discovery when the user requests
it. Ingest findings here to distinguish a validated designed boundary from an
accidental defence, assign impact and ownership, and stop autonomous changes
when policy or boundary redesign is needed. A currently unexploitable path can
still be an actionable boundary defect.

### Cleanliness and dead code

Ask the cleanliness skill for stale, duplicate, unused, and dependency hygiene
evidence. Before a deletion task, require reachability, migration, public API,
compatibility, and external caller evidence. If unexplained code carries a
privilege or invariant, route it here for architecture or security review.

### Implementation

Give the implementation agent one approved bounded task. Include non-goals and
the two-part verification requirement. The implementation agent must report
changed paths, test commands, and failures; it must not broaden scope or infer
human approval.

### Deployment and external action

For bundle contents, OAuth, vendor APIs, dashboards, credentials, deployed
configuration, or browser-only behaviour, create `VERIFY_FIRST` or
`HUMAN_ACTION_REQUIRED`. State who runs the check, what evidence is returned,
and when a failure is converted into a fix. Do not fake external verification
from static source.

### GitHub lifecycle

After verification and owner authorisation, hand off to the safe GitHub skill for
payload, hook, author, secret, history, and exact-revision gates. Review Gate
does not commit, push, merge, or open a pull request itself.

## Return contract

The companion must return:

- exact files or external systems touched;
- revision and command evidence;
- tests and verification outcomes;
- unresolved risks, decisions, and blockers;
- whether mutation or publication remains unauthorised.

Review Gate records the result as a finding/decision/verification update only
through the owner-approved state workflow. A handoff completion claim is
evidence, not final verification; inspect the returned evidence and compare the
recorded revision before closing an item.

## Anti-patterns

Stop and report if a handoff asks to:

- merge scanner severity with autonomy;
- delete a path because `rg` found no local caller;
- weaken security or a test to make the suite green;
- patch an external/runtime uncertainty without running the check;
- translate or approve legal/privacy/brand copy autonomously;
- treat a recommendation, prior unrelated approval, or silence as permission;
- write review state in the skill package or mutate the state during comparison;
- commit, push, deploy, or configure an external service without the dedicated
  safety gates.

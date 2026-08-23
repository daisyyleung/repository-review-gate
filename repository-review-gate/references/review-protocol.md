# Review protocol

Use this protocol to perform a bounded, evidence-led review. It complements
the compact workflow in `SKILL.md`; it does not grant mutation, publication, or
specialised scanner authority.

## Contents

- [Preflight](#preflight)
- [Authority map](#authority-map)
- [Evidence acquisition](#evidence-acquisition)
- [Validation](#validation)
- [Explanation](#explanation)
- [Testing quality](#testing-quality)
- [Report](#report)
- [Repeat review](#repeat-review)

## Preflight

Record:

1. repository identity and root;
2. source revision or immutable identifier;
3. requested scope and exclusions;
4. review start time and tool versions;
5. applicable repository instructions and human constraints;
6. previous review state location and whether this is a baseline;
7. available runtime, build, browser, deployment, and scanner evidence.

Read the nearest `AGENTS.md` before source files. Route to narrower project
indexes and canonical architecture or decision documents when they exist. Do
not scan unrelated vault or history content once authoritative context is
enough. If two sources both claim authority with no accepted decision resolving
the conflict, stop dependent remediation and create a decision item.

## Authority map

Create a concise table or note with one row per invariant:

| Invariant | Candidate authorities | Enforced where | Evidence revision | Conflict |
| --- | --- | --- | --- | --- |
| Authentication | route, middleware, provider | symbol/config | revision | yes/no |
| Tenant isolation | DB policy, service layer | migration/query | revision | yes/no |
| State transition | DB function, domain module | function/test | revision | yes/no |
| Persistence | schema, ORM, API | migration/model | revision | yes/no |
| Provider/config | env, config, fallback | loader/callers | revision | yes/no |
| Public contract | docs, route, response | test/deploy | revision | yes/no |

An authority map is an observation, not permission to consolidate. A duplicate
implementation may be a compatibility adapter, migration dependency, public
API, or reserved extension. Require reachability and contract evidence before
calling code dead.

## Evidence acquisition

Normalise each candidate into a finding input. Capture:

- stable ID (or a temporary ID until validation);
- title, category, and affected files/symbols or line ranges;
- source, revision, and scope for every evidence item;
- exact observation and reproduction steps;
- expected versus actual behaviour;
- confidence and explicit unknowns;
- source scanner/report ID when imported.

Evidence may be repository source, tests, configuration, logs, a scanner report,
or a human observation. Record inference separately from direct observation.
Do not claim runtime facts from static text alone. A deployment or external API
question becomes `VERIFY_FIRST` with a concrete method and pass/fail conversion
criteria. Do not embed credentials, user-home paths, client data, or secrets in
the record.

## Validation

Validate before explaining or prioritising:

1. Confirm the source path and symbol exist at the recorded revision.
2. Confirm the observed branch is reachable under the stated inputs.
3. Check whether a newer change, configuration, or approved decision supersedes
   the report.
4. Reproduce the failure or identify the exact missing runtime proof.
5. Deduplicate equivalent IDs and retain the strongest evidence.
6. Check claims against the authority map and documentation contracts.
7. Mark stale, obsolete, or unsupported reports as `NO_ACTION` with rationale.

Validation is not a fix. If validation requires a mutation, request a human
gate or use a disposable, explicitly authorised environment. Preserve original
state and keep any verification artefact separate from the reviewed repository.

## Explanation

Use two audiences without changing the facts.

### Technical explanation

Include finding ID, category, priority, confidence, files and symbols, evidence,
root cause, affected path, proposed bounded fix, non-goals, acceptance criteria,
verification method, decision dependencies, and status. Identify whether the
problem is current, latent, or unknown.

### Plain-language explanation

Answer in short sentences:

- What happened?
- Who or what is affected?
- Why does it matter?
- Is there immediate danger: yes, no, or unknown?
- Can an agent technically fix it?
- Must an owner choose or act?
- What will prove the result?

Do not hide uncertainty behind reassuring language. “Currently blocked by an
unrelated control” still means the designed control is broken. “Tests pass” does
not mean a user journey is proven.

## Testing quality

Classify the strongest available proof:

| Level | Proof | Limits |
| --- | --- | --- |
| 0 | Presence/source assertion | Text exists; behaviour untested |
| 1 | Structural assertion | Shape or wiring; execution untested |
| 2 | Behavioural test | Executed path and outcome |
| 3 | Boundary test | Auth, tenant, policy, or trust boundary |
| 4 | End-to-end/real integration | Deployed or real dependency behaviour |

Match test level to repository claim. For a runtime bug, prefer a behavioural
test. For auth or tenant isolation, require a boundary test when feasible. For
OAuth, vendor APIs, deployment bundles, migration reset, or browser-only
accessibility, use real integration or a documented verification task. If only
source assertions are possible, state exactly what remains unproven and mark
the verification quality degraded.

Reject a test that only makes a failing string disappear, weakens a security
assertion, mocks the branch under review, or tests the implementation rather
than the public contract. Retain both success and failure acceptance paths.

## Report

An executive report should contain:

1. scope, revision, and evidence limits;
2. overall risk and counts by priority and action route;
3. new, resolved, reopened, and deferred findings;
4. human decisions required, each with recommendation and alternatives;
5. verification queue with owner, method, and conversion rule;
6. bounded authorised work, explicit non-goals, and test requirements;
7. no-action and accepted-risk rationale;
8. next step that does not imply unauthorised mutation.

Group remediation by narrow risk or decision boundary, not by a large count of
unrelated findings. Every generated task should close or update one finding and
name the evidence it will produce.

## Repeat review

On a baseline review, capture the authority map, contracts, findings, decisions,
verification queue, and test maturity. On subsequent reviews:

- load prior statuses and approved decisions first;
- compare stable IDs and the repository revision;
- report new, resolved, reopened, and unchanged findings;
- check for regressions against approved decisions;
- re-run focused full-risk checks for changed areas;
- preserve prior records and append the new review entry.

Do not close an item merely because its file moved, scanner output changed
format, or a branch is currently unreachable without evidence of the contract.
If a decision is superseded, retain the old status, rationale, and successor
link. If a previously closed finding reappears, mark it reopened and explain
the changed evidence.

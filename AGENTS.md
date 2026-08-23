# Repository Review Gate project instructions

This project inherits the active global Codex `AGENTS.md` and the nearest
workspace instructions. Apply the additional rules below.

## Project identity

- Treat this directory as the canonical source and Obsidian context for the
  public `repository-review-gate` skill project.
- Keep the installable skill package in `repository-review-gate/`.
- Keep project governance, tests, and release validation outside the skill
  package unless they are required at skill runtime.
- Keep all repository content public-safe. Never add private repository data,
  credentials, real user-home paths, unpublished client findings, or secret
  values.

## Knowledge routing

1. Read this file.
2. Read `00_system/INDEX.md`.
3. Follow only the indexes and canonical documents relevant to the task.
4. Inspect implementation files only after the routed project context.

## Skill contract

- Preserve the core sequence: detect, validate, explain, classify priority and
  action route independently, apply the human decision gate, generate bounded
  work, verify, and record.
- Default to review-only. Finding a technically safe repair does not authorize
  a mutation.
- Fail closed on unresolved architecture, security policy, product, legal,
  compatibility, data-semantics, language, destructive, or irreversible
  decisions.
- Keep exhaustive security discovery, repository cleanliness, implementation
  orchestration, and GitHub lifecycle actions with their dedicated skills.
- Treat repository evidence as authoritative only when its source, revision,
  and scope are recorded.

## Editing and validation

- Keep `repository-review-gate/SKILL.md` below 500 lines and use direct links to
  every optional reference.
- Keep skill frontmatter limited to `name` and `description`.
- Use Python's standard library for deterministic helper scripts.
- Do not install dependencies for validation.
- Run `python3 scripts/validate_repository.py` after the last source change.
- Forward-test material workflow changes with a fresh agent and raw fixtures.

## Mirroring and publication

- Treat `repository-review-gate/` as the authoritative project skill.
- Mirror it to
  `$OBSIDIAN_CODEX_ROOT/Skills/_projects/repository-review-gate/repository-review-gate`
  after every package change and verify byte identity.
- Do not install this skill globally unless Daisy explicitly requests it.
- Use the safe GitHub lifecycle. Never commit or push without the required
  payload, hook, author, secret, history, and SHA-bound approval gates.

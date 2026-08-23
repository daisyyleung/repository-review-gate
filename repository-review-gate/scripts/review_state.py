#!/usr/bin/env python3
"""Read-only validation and comparison for ``.repo-review`` state.

The module intentionally uses only the Python standard library.  It never
creates, migrates, rewrites, deletes, commits, or publishes state.  Use the
explicit ``validate`` and ``diff`` subcommands for deterministic JSON output.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable

SCHEMA_VERSION = 1
STATE_FILES = (
    "manifest.json",
    "reviews.json",
    "findings.json",
    "decisions.json",
    "verifications.json",
)
ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9._:-]*$")

PRIORITIES = {"P0", "P1", "P2", "P3", "UNASSESSED"}
OWNERSHIPS = {
    "AUTO_FIXABLE",
    "HUMAN_DECISION_REQUIRED",
    "VERIFY_FIRST",
    "HUMAN_ACTION_REQUIRED",
    "ADVISORY",
    "NO_ACTION",
}
CONFIDENCES = {"LOW", "MEDIUM", "HIGH"}
MANIFEST_STATUSES = {"RUNNING", "COMPLETE", "FAILED", "ABORTED"}
REVIEW_STATUSES = MANIFEST_STATUSES
FINDING_STATUSES = {
    "DETECTED",
    "VALIDATED",
    "CLASSIFIED",
    "WAITING_FOR_HUMAN",
    "APPROVED",
    "VERIFY_PENDING",
    "READY_TO_FIX",
    "FIXED",
    "VERIFIED",
    "DEFERRED",
    "CLOSED",
    "REOPENED",
}
DECISION_STATUSES = {
    "OPEN",
    "APPROVED",
    "DEFERRED",
    "REJECTED",
    "SUPERSEDED",
    "REOPENED",
}
VERIFICATION_STATUSES = {"PENDING", "PASSED", "FAILED", "BLOCKED", "SUPERSEDED"}

FINDING_TRANSITIONS = {
    "DETECTED": {"VALIDATED", "CLOSED"},
    "VALIDATED": {"CLASSIFIED", "CLOSED"},
    "CLASSIFIED": {"WAITING_FOR_HUMAN", "VERIFY_PENDING", "READY_TO_FIX", "CLOSED"},
    "WAITING_FOR_HUMAN": {"APPROVED", "DEFERRED", "CLOSED"},
    "APPROVED": {"READY_TO_FIX", "WAITING_FOR_HUMAN", "DEFERRED"},
    "VERIFY_PENDING": {"VALIDATED", "CLASSIFIED", "CLOSED"},
    "READY_TO_FIX": {"FIXED", "DEFERRED"},
    "FIXED": {"VERIFIED", "READY_TO_FIX"},
    "VERIFIED": {"CLOSED", "REOPENED"},
    "DEFERRED": {"WAITING_FOR_HUMAN", "READY_TO_FIX", "REOPENED", "CLOSED"},
    "CLOSED": {"REOPENED"},
    "REOPENED": {"VALIDATED", "CLASSIFIED", "WAITING_FOR_HUMAN", "VERIFY_PENDING"},
}
DECISION_TRANSITIONS = {
    "OPEN": {"APPROVED", "DEFERRED", "REJECTED"},
    "APPROVED": {"REOPENED", "SUPERSEDED"},
    "DEFERRED": {"OPEN", "APPROVED", "REJECTED"},
    "REJECTED": {"REOPENED", "SUPERSEDED"},
    "REOPENED": {"OPEN", "APPROVED", "REJECTED"},
    "SUPERSEDED": set(),
}
VERIFICATION_TRANSITIONS = {
    "PENDING": {"PASSED", "FAILED", "BLOCKED", "SUPERSEDED"},
    "BLOCKED": {"PENDING", "SUPERSEDED"},
    "FAILED": {"PENDING", "SUPERSEDED"},
    "PASSED": {"SUPERSEDED"},
    "SUPERSEDED": set(),
}


def _error(errors: list[str], message: str) -> None:
    errors.append(message)


def _nonempty_string(value: Any, field: str, errors: list[str]) -> bool:
    if not isinstance(value, str) or not value.strip():
        _error(errors, f"{field}: expected a non-empty string")
        return False
    return True


def _valid_id(value: Any, field: str, errors: list[str]) -> bool:
    if not _nonempty_string(value, field, errors):
        return False
    if not ID_RE.fullmatch(value):
        _error(errors, f"{field}: invalid ID syntax")
        return False
    return True


def _list(value: Any, field: str, errors: list[str]) -> list[Any] | None:
    if not isinstance(value, list):
        _error(errors, f"{field}: expected an array")
        return None
    return value


def _enum(value: Any, allowed: set[str], field: str, errors: list[str]) -> bool:
    if not isinstance(value, str) or value not in allowed:
        _error(errors, f"{field}: unsupported enum value {value!r}")
        return False
    return True


def _load_json(path: Path, errors: list[str]) -> dict[str, Any] | None:
    try:
        with path.open("r", encoding="utf-8") as handle:
            value = json.load(handle)
    except FileNotFoundError:
        _error(errors, f"{path.name}: required file is missing")
        return None
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        _error(errors, f"{path.name}: cannot read JSON ({exc})")
        return None
    if not isinstance(value, dict):
        _error(errors, f"{path.name}: top level must be an object")
        return None
    version = value.get("schema_version")
    if version != SCHEMA_VERSION or isinstance(version, bool):
        _error(errors, f"{path.name}: schema_version must be integer {SCHEMA_VERSION}")
    return value


def _check_top_level(value: dict[str, Any], filename: str, collection: str, errors: list[str]) -> list[Any]:
    items = value.get(collection)
    if not isinstance(items, list):
        _error(errors, f"{filename}: {collection} must be an array")
        return []
    return items


def _check_transition(
    item: dict[str, Any],
    field: str,
    allowed_values: set[str],
    transitions: dict[str, set[str]],
    location: str,
    errors: list[str],
) -> None:
    current = item.get(field)
    if not _enum(current, allowed_values, f"{location}.{field}", errors):
        return
    previous = item.get("previous_status")
    if previous is not None:
        if _enum(previous, allowed_values, f"{location}.previous_status", errors) and current not in transitions[previous]:
            _error(errors, f"{location}: illegal transition {previous} -> {current}")
    history = item.get("status_history")
    if history is None:
        return
    if not isinstance(history, list) or not history:
        _error(errors, f"{location}.status_history: expected a non-empty array")
        return
    for index, value in enumerate(history):
        _enum(value, allowed_values, f"{location}.status_history[{index}]", errors)
    if all(isinstance(value, str) and value in allowed_values for value in history):
        if history[-1] != current:
            _error(errors, f"{location}.status_history: final entry must equal current status")
        for before, after in zip(history, history[1:]):
            if after not in transitions[before]:
                _error(errors, f"{location}.status_history: illegal transition {before} -> {after}")


def _check_evidence(value: Any, field: str, errors: list[str], required: bool = True) -> None:
    if value is None and not required:
        return
    entries = _list(value, field, errors)
    if entries is None:
        return
    if required and not entries:
        _error(errors, f"{field}: at least one evidence item is required")
    for index, evidence in enumerate(entries):
        location = f"{field}[{index}]"
        if not isinstance(evidence, dict):
            _error(errors, f"{location}: expected an object")
            continue
        for key in ("source", "revision", "scope", "detail"):
            _nonempty_string(evidence.get(key), f"{location}.{key}", errors)


def _check_id_array(item: dict[str, Any], key: str, location: str, known: set[str], errors: list[str]) -> None:
    value = item.get(key)
    if value is None:
        return
    values = _list(value, f"{location}.{key}", errors)
    if values is None:
        return
    for index, reference in enumerate(values):
        field = f"{location}.{key}[{index}]"
        if _valid_id(reference, field, errors) and reference not in known:
            _error(errors, f"{field}: dangling reference {reference!r}")


def _check_repository_identity(item: dict[str, Any], location: str, repository_id: str, errors: list[str]) -> None:
    value = item.get("repository_id")
    if value is not None and value != repository_id:
        _error(errors, f"{location}.repository_id: wrong repository identity {value!r}")


def validate_state(state_dir: str | Path, expected_repository_id: str | None = None) -> dict[str, Any]:
    """Validate one explicit state directory and return a stable result object."""

    root = Path(state_dir)
    errors: list[str] = []
    warnings: list[str] = []
    if not root.exists():
        _error(errors, "state directory does not exist")
        return {"command": "validate", "valid": False, "errors": sorted(errors), "warnings": warnings}
    if not root.is_dir():
        _error(errors, "state path is not a directory")
        return {"command": "validate", "valid": False, "errors": sorted(errors), "warnings": warnings}

    data: dict[str, dict[str, Any]] = {}
    for filename in STATE_FILES:
        loaded = _load_json(root / filename, errors)
        if loaded is not None:
            data[filename] = loaded
    if errors:
        return {"command": "validate", "valid": False, "errors": sorted(errors), "warnings": warnings}

    manifest = data["manifest.json"]
    repository = manifest.get("repository")
    if not isinstance(repository, dict):
        _error(errors, "manifest.json.repository: expected an object")
        repository = {}
    for key in ("id", "root", "revision"):
        _nonempty_string(repository.get(key), f"manifest.json.repository.{key}", errors)
    repository_id = repository.get("id") if isinstance(repository.get("id"), str) else ""
    if expected_repository_id is not None and repository_id != expected_repository_id:
        _error(errors, f"manifest.json.repository.id: expected {expected_repository_id!r}, got {repository_id!r}")
    _valid_id(manifest.get("review_id"), "manifest.json.review_id", errors)
    _enum(manifest.get("status"), MANIFEST_STATUSES, "manifest.json.status", errors)

    collections = {
        "reviews.json": _check_top_level(data["reviews.json"], "reviews.json", "reviews", errors),
        "findings.json": _check_top_level(data["findings.json"], "findings.json", "findings", errors),
        "decisions.json": _check_top_level(data["decisions.json"], "decisions.json", "decisions", errors),
        "verifications.json": _check_top_level(data["verifications.json"], "verifications.json", "verifications", errors),
    }
    entities: dict[str, dict[str, Any]] = {}
    locations: dict[str, str] = {}
    for filename, items in collections.items():
        kind = filename.removesuffix(".json")
        for index, item in enumerate(items):
            location = f"{filename}.{kind}[{index}]"
            if not isinstance(item, dict):
                _error(errors, f"{location}: expected an object")
                continue
            item_id = item.get("id")
            if not _valid_id(item_id, f"{location}.id", errors):
                continue
            if item_id in entities:
                _error(errors, f"{location}.id: duplicate ID {item_id!r} (already at {locations[item_id]})")
            else:
                entities[item_id] = item
                locations[item_id] = location
            _check_repository_identity(item, location, repository_id, errors)

    review_items = collections["reviews.json"]
    review_ids = {item.get("id") for item in review_items if isinstance(item, dict) and isinstance(item.get("id"), str)}
    finding_ids = {item.get("id") for item in collections["findings.json"] if isinstance(item, dict) and isinstance(item.get("id"), str)}
    decision_ids = {item.get("id") for item in collections["decisions.json"] if isinstance(item, dict) and isinstance(item.get("id"), str)}
    verification_ids = {item.get("id") for item in collections["verifications.json"] if isinstance(item, dict) and isinstance(item.get("id"), str)}
    decisions_by_id = {
        item["id"]: item
        for item in collections["decisions.json"]
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }

    if manifest.get("review_id") not in review_ids:
        _error(errors, "manifest.json.review_id: does not reference a review")

    for index, item in enumerate(review_items):
        if not isinstance(item, dict):
            continue
        location = f"reviews.json.reviews[{index}]"
        for key in ("repository_id", "revision"):
            _nonempty_string(item.get(key), f"{location}.{key}", errors)
        _enum(item.get("status"), REVIEW_STATUSES, f"{location}.status", errors)
        for key, known in (("finding_ids", finding_ids), ("decision_ids", decision_ids), ("verification_ids", verification_ids)):
            _check_id_array(item, key, location, known, errors)

    for index, item in enumerate(collections["findings.json"]):
        if not isinstance(item, dict):
            continue
        location = f"findings.json.findings[{index}]"
        for key in ("title", "category", "verification_method"):
            _nonempty_string(item.get(key), f"{location}.{key}", errors)
        _enum(item.get("priority"), PRIORITIES, f"{location}.priority", errors)
        # ``action_route`` is the canonical machine name; ``ownership`` remains
        # a backwards-compatible user-facing alias for imported records.
        route = item.get("action_route", item.get("ownership"))
        _enum(route, OWNERSHIPS, f"{location}.action_route", errors)
        if "action_route" in item and "ownership" in item and item["action_route"] != item["ownership"]:
            _error(errors, f"{location}: action_route and ownership disagree")
        _enum(item.get("confidence"), CONFIDENCES, f"{location}.confidence", errors)
        _check_transition(item, "status", FINDING_STATUSES, FINDING_TRANSITIONS, location, errors)
        _check_evidence(item.get("evidence"), f"{location}.evidence", errors)
        criteria = _list(item.get("acceptance_criteria"), f"{location}.acceptance_criteria", errors)
        if criteria is not None:
            if not criteria:
                _error(errors, f"{location}.acceptance_criteria: at least one criterion is required")
            for criterion_index, criterion in enumerate(criteria):
                _nonempty_string(criterion, f"{location}.acceptance_criteria[{criterion_index}]", errors)
        dependencies = item.get("dependencies", item.get("depends_on", []))
        if dependencies is not None:
            dependency_values = _list(dependencies, f"{location}.dependencies", errors)
            if dependency_values is not None:
                for dependency_index, dependency in enumerate(dependency_values):
                    field = f"{location}.dependencies[{dependency_index}]"
                    if _valid_id(dependency, field, errors) and dependency not in finding_ids:
                        _error(errors, f"{field}: dangling dependency {dependency!r}")
        decision_dependency = item.get("decision_dependency")
        decision_dependencies: list[Any] = []
        if decision_dependency is not None:
            decision_dependencies = decision_dependency if isinstance(decision_dependency, list) else [decision_dependency]
            for decision_index, dependency in enumerate(decision_dependencies):
                field = f"{location}.decision_dependency[{decision_index}]"
                if _valid_id(dependency, field, errors) and dependency not in decision_ids:
                    _error(errors, f"{field}: dangling decision reference {dependency!r}")
        if route == "HUMAN_DECISION_REQUIRED" and not decision_dependencies:
            _error(errors, f"{location}.decision_dependency: human-gated finding requires a decision reference")
        if route == "HUMAN_DECISION_REQUIRED":
            for dependency in decision_dependencies:
                decision = decisions_by_id.get(dependency)
                if decision is not None and item.get("id") not in decision.get("affected_findings", []):
                    _error(
                        errors,
                        f"{location}: decision {dependency!r} does not name affected finding {item.get('id')!r}",
                    )
        if route == "HUMAN_DECISION_REQUIRED" and item.get("status") in {
            "APPROVED",
            "READY_TO_FIX",
            "FIXED",
            "VERIFIED",
        }:
            for dependency in decision_dependencies:
                decision = decisions_by_id.get(dependency)
                if decision is not None and decision.get("status") != "APPROVED":
                    _error(
                        errors,
                        f"{location}: unresolved decision {dependency!r} blocks status {item.get('status')}",
                    )
        if route in {"VERIFY_FIRST", "HUMAN_ACTION_REQUIRED"} and item.get("status") in {
            "READY_TO_FIX",
            "FIXED",
            "VERIFIED",
        }:
            _error(errors, f"{location}: action route {route} requires reclassification before remediation")
        review_id = item.get("review_id")
        if review_id is not None and review_id not in review_ids:
            _error(errors, f"{location}.review_id: dangling review reference {review_id!r}")

    for index, item in enumerate(collections["decisions.json"]):
        if not isinstance(item, dict):
            continue
        location = f"decisions.json.decisions[{index}]"
        for key in ("title", "problem", "why_ai_cannot_decide", "recommended_option"):
            _nonempty_string(item.get(key), f"{location}.{key}", errors)
        for key in ("options", "tradeoffs", "affected_findings"):
            values = _list(item.get(key), f"{location}.{key}", errors)
            if values is not None and not values:
                _error(errors, f"{location}.{key}: at least one value is required")
            if values is not None and key != "affected_findings":
                for value_index, value in enumerate(values):
                    _nonempty_string(value, f"{location}.{key}[{value_index}]", errors)
        options = item.get("options")
        recommendation = item.get("recommended_option")
        if isinstance(options, list) and recommendation not in options:
            _error(errors, f"{location}.recommended_option: must identify one of the options")
        _check_transition(item, "status", DECISION_STATUSES, DECISION_TRANSITIONS, location, errors)
        _check_id_array(item, "affected_findings", location, finding_ids, errors)
        if item.get("status") == "APPROVED":
            for key in ("decision", "rationale", "approved_by", "approved_at_revision"):
                _nonempty_string(item.get(key), f"{location}.{key}", errors)
            if isinstance(options, list) and item.get("decision") not in options:
                _error(errors, f"{location}.decision: approved value must identify one of the options")
        successor = item.get("successor_id")
        if successor is not None and _valid_id(successor, f"{location}.successor_id", errors) and successor not in decision_ids:
            _error(errors, f"{location}.successor_id: dangling decision reference {successor!r}")
        review_id = item.get("review_id")
        if review_id is not None and review_id not in review_ids:
            _error(errors, f"{location}.review_id: dangling review reference {review_id!r}")

    for index, item in enumerate(collections["verifications.json"]):
        if not isinstance(item, dict):
            continue
        location = f"verifications.json.verifications[{index}]"
        _valid_id(item.get("finding_id"), f"{location}.finding_id", errors)
        if item.get("finding_id") not in finding_ids:
            _error(errors, f"{location}.finding_id: dangling finding reference {item.get('finding_id')!r}")
        _nonempty_string(item.get("method"), f"{location}.method", errors)
        _check_transition(item, "status", VERIFICATION_STATUSES, VERIFICATION_TRANSITIONS, location, errors)
        _check_evidence(item.get("evidence"), f"{location}.evidence", errors, required=item.get("status") in {"PASSED", "FAILED"})
        review_id = item.get("review_id")
        if review_id is not None and review_id not in review_ids:
            _error(errors, f"{location}.review_id: dangling review reference {review_id!r}")

    result: dict[str, Any] = {
        "command": "validate",
        "valid": not errors,
        "errors": sorted(set(errors)),
        "warnings": sorted(set(warnings)),
        "repository_id": repository_id,
    }
    return result


def _read_validated(state_dir: str | Path) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    result = validate_state(state_dir)
    if not result["valid"]:
        return None, result
    root = Path(state_dir)
    data: dict[str, Any] = {}
    for filename in STATE_FILES:
        with (root / filename).open("r", encoding="utf-8") as handle:
            data[filename] = json.load(handle)
    return data, result


def _items(data: dict[str, Any], filename: str, key: str) -> dict[str, dict[str, Any]]:
    values = data[filename].get(key, [])
    return {item["id"]: item for item in values if isinstance(item, dict) and isinstance(item.get("id"), str)}


def _action_route(item: dict[str, Any]) -> Any:
    """Return the canonical route across current and legacy field names."""

    return item.get("action_route", item.get("ownership"))


def diff_states(previous_dir: str | Path, current_dir: str | Path) -> dict[str, Any]:
    """Compare two valid state directories without considering timestamps or order."""

    previous, previous_result = _read_validated(previous_dir)
    current, current_result = _read_validated(current_dir)
    errors = []
    if not previous_result["valid"]:
        errors.extend(f"previous: {error}" for error in previous_result["errors"])
    if not current_result["valid"]:
        errors.extend(f"current: {error}" for error in current_result["errors"])
    if previous and current:
        previous_repo = previous["manifest.json"].get("repository", {}).get("id")
        current_repo = current["manifest.json"].get("repository", {}).get("id")
        if previous_repo != current_repo:
            errors.append(f"repository identity differs: {previous_repo!r} != {current_repo!r}")
    if errors:
        return {"command": "diff", "valid": False, "errors": sorted(set(errors))}

    old_findings = _items(previous, "findings.json", "findings")
    new_findings = _items(current, "findings.json", "findings")
    old_ids = set(old_findings)
    new_ids = set(new_findings)
    new_finding_ids = sorted(new_ids - old_ids)
    resolved_ids = sorted(
        finding_id
        for finding_id in old_ids & new_ids
        if old_findings[finding_id].get("status") != "CLOSED" and new_findings[finding_id].get("status") == "CLOSED"
    )
    reopened_ids = sorted(
        finding_id
        for finding_id in old_ids & new_ids
        if old_findings[finding_id].get("status") == "CLOSED"
        and new_findings[finding_id].get("status") != "CLOSED"
    )
    changed_ids = sorted(
        finding_id
        for finding_id in old_ids & new_ids
        if (
            any(
                old_findings[finding_id].get(key) != new_findings[finding_id].get(key)
                for key in ("status", "priority")
            )
            or _action_route(old_findings[finding_id]) != _action_route(new_findings[finding_id])
        )
    )

    old_decisions = _items(previous, "decisions.json", "decisions")
    new_decisions = _items(current, "decisions.json", "decisions")
    old_decision_ids = set(old_decisions)
    new_decision_ids = set(new_decisions)
    decision_delta: dict[str, list[str]] = {
        "new": sorted(new_decision_ids - old_decision_ids),
        "approved": [],
        "reopened": [],
        "deferred": [],
        "rejected": [],
        "superseded": [],
        "changed": [],
    }
    for decision_id in sorted(old_decision_ids & new_decision_ids):
        before = old_decisions[decision_id]
        after = new_decisions[decision_id]
        before_status = before.get("status")
        after_status = after.get("status")
        if before_status != after_status or before.get("decision") != after.get("decision"):
            decision_delta["changed"].append(decision_id)
        if before_status != after_status and after_status in {"APPROVED", "REOPENED", "DEFERRED", "REJECTED", "SUPERSEDED"}:
            decision_delta[after_status.lower()].append(decision_id)

    return {
        "command": "diff",
        "valid": True,
        "errors": [],
        "repository_id": current["manifest.json"].get("repository", {}).get("id"),
        "new_findings": new_finding_ids,
        "resolved_findings": resolved_ids,
        "reopened_findings": reopened_ids,
        "changed_findings": changed_ids,
        # Short aliases keep integrations written against the plain
        # new/resolved/reopened vocabulary interoperable with the explicit
        # finding-prefixed fields above.
        "new": new_finding_ids,
        "resolved": resolved_ids,
        "reopened": reopened_ids,
        "decision_deltas": decision_delta,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate or diff repository review state without mutating it")
    commands = parser.add_subparsers(dest="command", required=True)
    validate_parser = commands.add_parser("validate", help="validate one explicit state directory")
    validate_parser.add_argument("state_dir", nargs="?", help="path to .repo-review state directory")
    validate_parser.add_argument("--state-dir", dest="state_dir_option", help="explicit path to .repo-review state directory")
    validate_parser.add_argument("--repository-id", dest="repository_id", help="expected repository identity")
    diff_parser = commands.add_parser("diff", help="compare two explicit state directories")
    diff_parser.add_argument("previous_dir", nargs="?", help="previous .repo-review state directory")
    diff_parser.add_argument("current_dir", nargs="?", help="current .repo-review state directory")
    diff_parser.add_argument("--previous-dir", dest="previous_dir_option", help="explicit previous state directory")
    diff_parser.add_argument("--current-dir", dest="current_dir_option", help="explicit current state directory")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = _parser().parse_args(list(argv) if argv is not None else None)
    if args.command == "validate":
        state_dir = args.state_dir_option or args.state_dir
        if not state_dir:
            _parser().error("validate requires an explicit state directory")
        result = validate_state(state_dir, args.repository_id)
    else:
        previous_dir = args.previous_dir_option or args.previous_dir
        current_dir = args.current_dir_option or args.current_dir
        if not previous_dir or not current_dir:
            _parser().error("diff requires two explicit state directories")
        result = diff_states(previous_dir, current_dir)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0 if result.get("valid") else 1


if __name__ == "__main__":
    raise SystemExit(main())

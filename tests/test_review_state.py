from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HELPER_PATH = ROOT / "repository-review-gate/scripts/review_state.py"
SPEC = importlib.util.spec_from_file_location("review_state", HELPER_PATH)
assert SPEC and SPEC.loader
review_state = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(review_state)


def _copy_fixture(destination: Path) -> Path:
    source = ROOT / "tests/fixtures/state-valid"
    target = destination / "state"
    shutil.copytree(source, target)
    return target


def _load(path: Path, filename: str) -> dict:
    return json.loads((path / filename).read_text(encoding="utf-8"))


def _write(path: Path, filename: str, value: dict) -> None:
    (path / filename).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _tree_hash(path: Path) -> dict[str, str]:
    return {
        str(file.relative_to(path)): hashlib.sha256(file.read_bytes()).hexdigest()
        for file in sorted(item for item in path.rglob("*") if item.is_file())
    }


class ReviewStateValidationTests(unittest.TestCase):
    def test_valid_state(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state_dir = _copy_fixture(Path(temporary))
            result = review_state.validate_state(state_dir)
            self.assertTrue(result["valid"], result)
            self.assertEqual(result["repository_id"], "fixture-repository")

    def test_action_route_is_accepted_as_canonical_alias(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state_dir = _copy_fixture(Path(temporary))
            findings = _load(state_dir, "findings.json")
            findings["findings"][0]["action_route"] = findings["findings"][0].pop("ownership")
            _write(state_dir, "findings.json", findings)
            result = review_state.validate_state(state_dir)
            self.assertTrue(result["valid"], result)

    def test_invalid_schema_is_nonzero_and_machine_readable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state_dir = _copy_fixture(Path(temporary))
            manifest = _load(state_dir, "manifest.json")
            manifest["schema_version"] = 99
            _write(state_dir, "manifest.json", manifest)
            result = review_state.validate_state(state_dir)
            self.assertFalse(result["valid"])
            self.assertTrue(any("schema_version" in error for error in result["errors"]))

    def test_wrong_repository_identity_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state_dir = _copy_fixture(Path(temporary))
            result = review_state.validate_state(state_dir, expected_repository_id="other-repository")
            self.assertFalse(result["valid"])
            self.assertTrue(any("expected 'other-repository'" in error for error in result["errors"]))

    def test_duplicate_ids_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state_dir = _copy_fixture(Path(temporary))
            reviews = _load(state_dir, "reviews.json")
            reviews["reviews"].append(dict(reviews["reviews"][0]))
            _write(state_dir, "reviews.json", reviews)
            result = review_state.validate_state(state_dir)
            self.assertFalse(result["valid"])
            self.assertTrue(any("duplicate ID 'REVIEW-001'" in error for error in result["errors"]))

    def test_dangling_dependency_and_decision_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state_dir = _copy_fixture(Path(temporary))
            findings = _load(state_dir, "findings.json")
            finding = findings["findings"][0]
            finding["dependencies"] = ["F-404"]
            finding["decision_dependency"] = "DECISION-404"
            _write(state_dir, "findings.json", findings)
            result = review_state.validate_state(state_dir)
            self.assertFalse(result["valid"])
            self.assertTrue(any("dangling dependency 'F-404'" in error for error in result["errors"]))
            self.assertTrue(any("dangling decision reference 'DECISION-404'" in error for error in result["errors"]))

    def test_illegal_transition_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state_dir = _copy_fixture(Path(temporary))
            findings = _load(state_dir, "findings.json")
            finding = findings["findings"][0]
            finding["previous_status"] = "DETECTED"
            finding["status"] = "READY_TO_FIX"
            _write(state_dir, "findings.json", findings)
            result = review_state.validate_state(state_dir)
            self.assertFalse(result["valid"])
            self.assertTrue(any("illegal transition DETECTED -> READY_TO_FIX" in error for error in result["errors"]))

    def test_approved_decision_requires_complete_approval_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state_dir = _copy_fixture(Path(temporary))
            decisions = {
                "schema_version": 1,
                "decisions": [
                    {
                        "id": "DECISION-001",
                        "title": "Choose authority",
                        "problem": "Two authorities disagree",
                        "why_ai_cannot_decide": "Architecture choice",
                        "recommended_option": "database",
                        "options": ["database", "application"],
                        "tradeoffs": ["Database centralises invariants", "Application is easier to iterate"],
                        "affected_findings": ["F-001"],
                        "status": "APPROVED",
                    }
                ],
            }
            _write(state_dir, "decisions.json", decisions)
            result = review_state.validate_state(state_dir)
            self.assertFalse(result["valid"])
            self.assertTrue(any("approved_by" in error for error in result["errors"]))

    def test_human_gated_finding_requires_a_decision_reference(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state_dir = _copy_fixture(Path(temporary))
            findings = _load(state_dir, "findings.json")
            finding = findings["findings"][0]
            finding["ownership"] = "HUMAN_DECISION_REQUIRED"
            finding["decision_dependency"] = None
            _write(state_dir, "findings.json", findings)
            result = review_state.validate_state(state_dir)
            self.assertFalse(result["valid"])
            self.assertTrue(any("requires a decision reference" in error for error in result["errors"]))

    def test_unresolved_human_decision_blocks_fix_ready_state(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state_dir = _copy_fixture(Path(temporary))
            findings = _load(state_dir, "findings.json")
            finding = findings["findings"][0]
            finding.update(
                {
                    "ownership": "HUMAN_DECISION_REQUIRED",
                    "decision_dependency": "DECISION-001",
                    "status": "READY_TO_FIX",
                }
            )
            _write(state_dir, "findings.json", findings)
            decisions = {
                "schema_version": 1,
                "decisions": [
                    {
                        "id": "DECISION-001",
                        "title": "Choose authority",
                        "problem": "Two authorities disagree",
                        "why_ai_cannot_decide": "Architecture choice",
                        "recommended_option": "database",
                        "options": ["database", "application"],
                        "tradeoffs": ["Database centralises invariants", "Application is easier to iterate"],
                        "affected_findings": ["F-001"],
                        "status": "OPEN",
                    }
                ],
            }
            _write(state_dir, "decisions.json", decisions)
            result = review_state.validate_state(state_dir)
            self.assertFalse(result["valid"])
            self.assertTrue(any("unresolved decision 'DECISION-001'" in error for error in result["errors"]))

    def test_unrelated_approved_decision_cannot_unblock_finding(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state_dir = _copy_fixture(Path(temporary))
            findings = _load(state_dir, "findings.json")
            finding = findings["findings"][0]
            finding.update(
                {
                    "ownership": "HUMAN_DECISION_REQUIRED",
                    "decision_dependency": "DECISION-001",
                    "status": "READY_TO_FIX",
                }
            )
            unrelated = dict(finding)
            unrelated.update({"id": "F-002", "ownership": "ADVISORY", "decision_dependency": None})
            findings["findings"].append(unrelated)
            _write(state_dir, "findings.json", findings)
            decisions = {
                "schema_version": 1,
                "decisions": [
                    {
                        "id": "DECISION-001",
                        "title": "Choose authority for another finding",
                        "problem": "Another authority conflict",
                        "why_ai_cannot_decide": "Architecture choice",
                        "recommended_option": "database",
                        "options": ["database", "application"],
                        "tradeoffs": ["Database centralises invariants", "Application is easier to iterate"],
                        "affected_findings": ["F-002"],
                        "status": "APPROVED",
                        "decision": "database",
                        "rationale": "Centralise invariants",
                        "approved_by": "owner",
                        "approved_at_revision": "rev-002",
                    }
                ],
            }
            _write(state_dir, "decisions.json", decisions)
            result = review_state.validate_state(state_dir)
            self.assertFalse(result["valid"])
            self.assertTrue(any("does not name affected finding 'F-001'" in error for error in result["errors"]))

    def test_verify_first_must_be_reclassified_before_remediation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state_dir = _copy_fixture(Path(temporary))
            findings = _load(state_dir, "findings.json")
            finding = findings["findings"][0]
            finding.update({"ownership": "VERIFY_FIRST", "status": "READY_TO_FIX"})
            _write(state_dir, "findings.json", findings)
            result = review_state.validate_state(state_dir)
            self.assertFalse(result["valid"])
            self.assertTrue(any("requires reclassification" in error for error in result["errors"]))

    def test_approved_decision_must_name_an_available_option(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state_dir = _copy_fixture(Path(temporary))
            decisions = {
                "schema_version": 1,
                "decisions": [
                    {
                        "id": "DECISION-001",
                        "title": "Choose authority",
                        "problem": "Two authorities disagree",
                        "why_ai_cannot_decide": "Architecture choice",
                        "recommended_option": "database",
                        "options": ["database", "application"],
                        "tradeoffs": ["Database centralises invariants", "Application is easier to iterate"],
                        "affected_findings": ["F-001"],
                        "status": "APPROVED",
                        "decision": "hybrid",
                        "rationale": "Keep both temporarily",
                        "approved_by": "owner",
                        "approved_at_revision": "rev-002",
                    }
                ],
            }
            _write(state_dir, "decisions.json", decisions)
            result = review_state.validate_state(state_dir)
            self.assertFalse(result["valid"])
            self.assertTrue(any("approved value must identify one of the options" in error for error in result["errors"]))


class ReviewStateDiffTests(unittest.TestCase):
    def _add_open_decision(self, state_dir: Path) -> None:
        decisions = {
            "schema_version": 1,
            "decisions": [
                {
                    "id": "DECISION-001",
                    "title": "Choose authority",
                    "problem": "Two authorities disagree",
                    "why_ai_cannot_decide": "Architecture choice",
                    "recommended_option": "database",
                    "options": ["database", "application"],
                    "tradeoffs": ["Database centralises invariants", "Application is easier to iterate"],
                    "affected_findings": ["F-001"],
                    "status": "OPEN",
                    "decision": None,
                    "rationale": None,
                }
            ],
        }
        _write(state_dir, "decisions.json", decisions)

    def test_diff_reports_new_resolved_reopened_and_decision_deltas(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            old = _copy_fixture(root / "old")
            self._add_open_decision(old)

            current = root / "current"
            shutil.copytree(old, current)
            findings = _load(current, "findings.json")
            findings["findings"][0]["status"] = "CLOSED"
            extra = dict(findings["findings"][0])
            extra["id"] = "F-002"
            extra["status"] = "CLASSIFIED"
            findings["findings"].append(extra)
            _write(current, "findings.json", findings)

            decisions = _load(current, "decisions.json")
            decision = decisions["decisions"][0]
            decision.update(
                {
                    "status": "APPROVED",
                    "decision": "database",
                    "rationale": "Centralise invariants",
                    "approved_by": "owner",
                    "approved_at_revision": "rev-002",
                }
            )
            _write(current, "decisions.json", decisions)

            first = review_state.diff_states(old, current)
            second = review_state.diff_states(old, current)
            self.assertTrue(first["valid"], first)
            self.assertEqual(first, second)
            self.assertEqual(first["new_findings"], ["F-002"])
            self.assertEqual(first["resolved_findings"], ["F-001"])
            self.assertEqual(first["reopened_findings"], [])
            self.assertEqual(first["decision_deltas"]["approved"], ["DECISION-001"])

            reopened = root / "reopened"
            shutil.copytree(current, reopened)
            reopened_findings = _load(reopened, "findings.json")
            reopened_findings["findings"][0]["status"] = "REOPENED"
            _write(reopened, "findings.json", reopened_findings)
            reopened_result = review_state.diff_states(current, reopened)
            self.assertEqual(reopened_result["reopened_findings"], ["F-001"])

    def test_diff_rejects_wrong_repository(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            old = _copy_fixture(root / "old")
            current = root / "current"
            shutil.copytree(old, current)
            manifest = _load(current, "manifest.json")
            manifest["repository"]["id"] = "other-repository"
            _write(current, "manifest.json", manifest)
            result = review_state.diff_states(old, current)
            self.assertFalse(result["valid"])
            self.assertTrue(
                any(
                    "repository identity differs" in error or "wrong repository identity" in error
                    for error in result["errors"]
                )
            )

    def test_alias_only_route_migration_is_not_a_changed_finding(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            old = _copy_fixture(root / "old")
            current = root / "current"
            shutil.copytree(old, current)
            findings = _load(current, "findings.json")
            finding = findings["findings"][0]
            finding["action_route"] = finding.pop("ownership")
            _write(current, "findings.json", findings)
            result = review_state.diff_states(old, current)
            self.assertTrue(result["valid"], result)
            self.assertEqual(result["changed_findings"], [])


class ReadOnlyAndCliTests(unittest.TestCase):
    def test_validation_and_diff_do_not_mutate_fixture(self) -> None:
        fixture_root = ROOT / "tests/fixtures"
        before = _tree_hash(fixture_root)
        valid = fixture_root / "state-valid"
        self.assertTrue(review_state.validate_state(valid)["valid"])
        self.assertTrue(review_state.diff_states(valid, valid)["valid"])
        self.assertEqual(before, _tree_hash(fixture_root))

    def test_cli_emits_json_and_nonzero_for_invalid_input(self) -> None:
        command = [sys.executable, str(HELPER_PATH), "validate", str(ROOT / "tests/fixtures/state-valid")]
        environment = os.environ.copy()
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        completed = subprocess.run(command, cwd=ROOT, env=environment, text=True, capture_output=True)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertTrue(payload["valid"])

        invalid = [sys.executable, str(HELPER_PATH), "validate", str(ROOT / "tests/fixtures/missing-state")]
        failed = subprocess.run(invalid, cwd=ROOT, env=environment, text=True, capture_output=True)
        self.assertNotEqual(failed.returncode, 0)
        self.assertFalse(json.loads(failed.stdout)["valid"])


if __name__ == "__main__":
    unittest.main()

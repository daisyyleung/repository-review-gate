from __future__ import annotations

import importlib.util
import re
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "repository-review-gate"
VALIDATOR_PATH = ROOT / "scripts/validate_repository.py"
VALIDATOR_SPEC = importlib.util.spec_from_file_location("validate_repository", VALIDATOR_PATH)
assert VALIDATOR_SPEC and VALIDATOR_SPEC.loader
validate_repository = importlib.util.module_from_spec(VALIDATOR_SPEC)
VALIDATOR_SPEC.loader.exec_module(validate_repository)


class SkillContractTests(unittest.TestCase):
    def test_skill_frontmatter_and_line_limit(self) -> None:
        text = (PACKAGE / "SKILL.md").read_text(encoding="utf-8")
        self.assertLess(len(text.splitlines()), 500)
        self.assertTrue(text.startswith("---\n"))
        frontmatter = text.split("\n---\n", 1)[0].removeprefix("---\n")
        keys = {line.split(":", 1)[0].strip() for line in frontmatter.splitlines() if line.strip()}
        self.assertEqual(keys, {"name", "description"})
        self.assertIn("repository-review-gate", frontmatter)

    def test_every_reference_is_directly_linked(self) -> None:
        text = (PACKAGE / "SKILL.md").read_text(encoding="utf-8")
        targets = {
            match.split("#", 1)[0]
            for match in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text)
            if match.startswith("references/")
        }
        expected = {path.relative_to(PACKAGE).as_posix() for path in (PACKAGE / "references").glob("*.md")}
        self.assertEqual(targets, expected)
        for target in targets:
            self.assertTrue((PACKAGE / target).is_file(), target)

    def test_forward_fixtures_cover_required_raw_scenarios(self) -> None:
        fixture_root = ROOT / "tests/fixtures/raw"
        expected = {
            "clear-correctness",
            "architecture-conflict",
            "runtime-uncertainty",
            "source-grep-test",
            "accidental-security-defence",
            "prior-approved-decision",
        }
        self.assertEqual({path.name for path in fixture_root.iterdir() if path.is_dir()}, expected)
        for directory in expected:
            self.assertTrue(any(path.is_file() for path in (fixture_root / directory).iterdir()), directory)


class PublicSafetyTests(unittest.TestCase):
    def test_git_internal_files_are_excluded_from_public_content_scan(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            machine_path = "/" + "Users" + "/daisy/project"
            (root / ".git").mkdir()
            (root / ".git" / "local-report.json").write_text(
                f'{{"root": "{machine_path}"}}', encoding="utf-8"
            )
            (root / "README.md").write_text(
                f'{{"root": "{machine_path}"}}', encoding="utf-8"
            )

            errors = validate_repository._check_public_safe(root)

        self.assertEqual(len(errors), 1)
        self.assertIn("README.md", errors[0])
        self.assertNotIn(".git/", errors[0])


if __name__ == "__main__":
    unittest.main()

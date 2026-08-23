from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "repository-review-gate"


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


if __name__ == "__main__":
    unittest.main()

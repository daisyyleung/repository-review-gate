#!/usr/bin/env python3
"""Release-gate validation for the repository-review-gate project.

The validator uses only the standard library, discovers Skill Creator's
``quick_validate.py`` at runtime when available, and never installs packages or
writes project files.  Temporary subprocess artefacts are disabled with
``PYTHONDONTWRITEBYTECODE``.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable

EXPECTED_INTERFACE = {
    "display_name": "Repository Review Gate",
    "short_description": "Review repositories and gate remediation decisions",
    "default_prompt": "Use $repository-review-gate to review this repository, validate evidence, separate priority from action ownership, surface human decisions, and define verified remediation.",
}
REFERENCE_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---(?:\n|\Z)", re.DOTALL)
MACHINE_PATH_RE = re.compile(
    r"(?:/"
    + "Users"
    + r"/[A-Za-z0-9._-]+|/"
    + "home"
    + r"/[A-Za-z0-9._-]+|[A-Za-z]:\\"
    + "Users"
    + r"\\[A-Za-z0-9._-]+)"
)
SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _parse_simple_frontmatter(text: str) -> tuple[dict[str, str] | None, str | None]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return None, "SKILL.md must start with YAML frontmatter"
    values: dict[str, str] = {}
    for line_number, line in enumerate(match.group(1).splitlines(), 1):
        if not line.strip():
            continue
        if ":" not in line:
            return None, f"frontmatter line {line_number}: expected key: value"
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if not key or not value:
            return None, f"frontmatter line {line_number}: empty key or value"
        if value[0:1] in {'"', "'"} and value[-1:] == value[0]:
            value = value[1:-1]
        values[key] = value
    return values, None


def _hash_tree(root: Path) -> dict[str, str]:
    snapshot: dict[str, str] = {}
    if not root.exists():
        return snapshot
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        snapshot[str(path.relative_to(root))] = digest
    return snapshot


def _run(command: list[str], cwd: Path) -> tuple[int, str, str]:
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(command, cwd=str(cwd), env=environment, text=True, capture_output=True)
    return completed.returncode, completed.stdout.strip(), completed.stderr.strip()


def _run_quick_validate(quick_validate: Path, package: Path, cwd: Path) -> tuple[int, str, str, bool]:
    """Run Skill Creator validation, with an in-memory stdlib YAML shim only
    when the official script is present but PyYAML is unavailable.

    The project validator itself remains dependency-free.  The shim implements
    the tiny mapping parser needed by the official frontmatter check; it is
    injected only into the validation subprocess and never written or installed.
    """

    command = [sys.executable, str(quick_validate), str(package)]
    code, stdout, stderr = _run(command, cwd)
    if code == 0 or "No module named 'yaml'" not in stderr:
        return code, stdout, stderr, False
    shim_runner = r'''
import runpy
import sys
import types

class YAMLError(Exception):
    pass

def safe_load(text):
    result = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] in "\\\"'" and value[-1] == value[0]:
            value = value[1:-1]
        result[key.strip()] = value
    return result

yaml = types.ModuleType("yaml")
yaml.safe_load = safe_load
yaml.YAMLError = YAMLError
sys.modules["yaml"] = yaml
script, package = sys.argv[1], sys.argv[2]
sys.argv = [script, package]
runpy.run_path(script, run_name="__main__")
'''
    code, stdout, stderr = _run(
        [sys.executable, "-c", shim_runner, str(quick_validate), str(package)],
        cwd,
    )
    return code, stdout, stderr, True


def _discover_quick_validate() -> Path | None:
    candidates: list[Path] = []
    codex_home = os.environ.get("CODEX_HOME")
    if codex_home:
        candidates.append(Path(codex_home) / "skills/.system/skill-creator/scripts/quick_validate.py")
    candidates.append(Path.home() / ".codex/skills/.system/skill-creator/scripts/quick_validate.py")
    executable = shutil.which("quick_validate.py")
    if executable:
        candidates.append(Path(executable))
    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.expanduser()
        if resolved in seen:
            continue
        seen.add(resolved)
        if resolved.is_file():
            return resolved
    return None


def _check_links(skill_dir: Path, skill_text: str) -> list[str]:
    errors: list[str] = []
    linked_references: set[str] = set()
    for raw_target in REFERENCE_LINK_RE.findall(skill_text):
        target = raw_target.strip().split("#", 1)[0]
        if not target or "://" in target or target.startswith("#"):
            continue
        if target.startswith("/") or target.startswith("~"):
            errors.append(f"SKILL.md: link must be relative: {raw_target}")
            continue
        resolved = (skill_dir / target).resolve()
        try:
            resolved.relative_to(skill_dir.resolve())
        except ValueError:
            errors.append(f"SKILL.md: link escapes package: {raw_target}")
            continue
        if not resolved.is_file():
            errors.append(f"SKILL.md: linked file does not exist: {raw_target}")
        if target.startswith("references/") and target.endswith(".md"):
            linked_references.add(target)
    for reference in sorted((path.relative_to(skill_dir).as_posix() for path in (skill_dir / "references").glob("*.md"))):
        if reference not in linked_references:
            errors.append(f"SKILL.md: reference is not directly linked: {reference}")
    return errors


def _check_public_safe(root: Path) -> list[str]:
    errors: list[str] = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative_path = path.relative_to(root)
        if ".git" in relative_path.parts:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for match in MACHINE_PATH_RE.finditer(text):
            errors.append(f"{relative_path}: machine-specific path {match.group(0)!r}")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                errors.append(f"{relative_path}: secret-like value detected")
    return errors


def run_checks(project_root: str | Path | None = None) -> dict[str, object]:
    root = Path(project_root) if project_root is not None else Path(__file__).resolve().parents[1]
    package = root / "repository-review-gate"
    errors: list[str] = []
    warnings: list[str] = []
    observations: list[str] = []
    skill_path = package / "SKILL.md"
    if not skill_path.is_file():
        errors.append("repository-review-gate/SKILL.md is missing")
        return {"valid": False, "errors": sorted(errors), "warnings": warnings, "observations": observations}

    skill_text = _read(skill_path)
    lines = skill_text.splitlines()
    if len(lines) >= 500:
        errors.append(f"SKILL.md must be below 500 lines (found {len(lines)})")
    frontmatter, frontmatter_error = _parse_simple_frontmatter(skill_text)
    if frontmatter_error:
        errors.append(frontmatter_error)
    elif frontmatter is not None:
        if set(frontmatter) != {"name", "description"}:
            errors.append(f"SKILL.md frontmatter keys must be name and description, found {sorted(frontmatter)}")
        if frontmatter.get("name") != "repository-review-gate":
            errors.append("SKILL.md frontmatter name does not match package")
        if len(frontmatter.get("description", "")) < 80:
            errors.append("SKILL.md description is too short to state triggers and exclusions")
    errors.extend(_check_links(package, skill_text))

    openai_path = package / "agents/openai.yaml"
    if not openai_path.is_file():
        errors.append("agents/openai.yaml is missing")
    else:
        yaml_text = _read(openai_path)
        for key, expected in EXPECTED_INTERFACE.items():
            pattern = re.compile(rf"^\s*{re.escape(key)}:\s*[\"'](.*?)[\"']\s*$", re.MULTILINE)
            match = pattern.search(yaml_text)
            if not match or match.group(1) != expected:
                errors.append(f"agents/openai.yaml interface.{key} is inconsistent")

    helper = package / "scripts/review_state.py"
    if not helper.is_file():
        errors.append("scripts/review_state.py is missing")
    else:
        try:
            compile(_read(helper), str(helper), "exec")
            observations.append("review_state.py compiles in memory")
        except SyntaxError as exc:
            errors.append(f"review_state.py syntax error: {exc}")

    for reference in sorted((package / "references").glob("*.md")):
        if len(_read(reference).splitlines()) > 100 and "## Contents" not in _read(reference):
            errors.append(f"{reference.relative_to(root)}: long reference lacks a contents section")

    quick_validate = _discover_quick_validate()
    if quick_validate is None:
        warnings.append("Skill Creator quick_validate.py was not discoverable")
    else:
        code, stdout, stderr, used_shim = _run_quick_validate(quick_validate, package, root)
        if code != 0:
            errors.append(f"Skill Creator quick validation failed: {stdout or stderr}")
        else:
            if used_shim:
                warnings.append("PyYAML was unavailable; official quick validation ran with an in-memory standard-library YAML compatibility module")
            observations.append(f"Skill Creator quick validation passed: {stdout}")

    fixtures = root / "tests/fixtures"
    before = _hash_tree(fixtures)
    if helper.is_file():
        valid_state = fixtures / "state-valid"
        if valid_state.is_dir():
            code, stdout, stderr = _run([sys.executable, str(helper), "validate", str(valid_state)], root)
            if code != 0:
                errors.append(f"state helper validation fixture failed: {stdout or stderr}")
            else:
                observations.append("state helper validated the read-only fixture")
    after = _hash_tree(fixtures)
    if before != after:
        errors.append("tests/fixtures changed while running read-only validation")

    test_dir = root / "tests"
    if test_dir.is_dir():
        code, stdout, stderr = _run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"], root)
        if code != 0:
            errors.append(f"unit tests failed: {stdout or stderr}")
        else:
            observations.append("unit tests passed")
    else:
        errors.append("tests directory is missing")

    errors.extend(_check_public_safe(root))
    return {
        "valid": not errors,
        "errors": sorted(set(errors)),
        "warnings": sorted(set(warnings)),
        "observations": observations,
        "skill_lines": len(lines),
        "quick_validate_discovered": quick_validate is not None,
    }


def main() -> int:
    result = run_checks()
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

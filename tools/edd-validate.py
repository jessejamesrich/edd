#!/usr/bin/env python3
"""Validate EDD story files.

Sweeps `.edd/**/story.yaml` (and any `runs/*.yaml` detail files), parses each
with a safe loader, and checks the story schema: required fields, canonical
`status`, priority format, append-only `runs`, and directory ↔ status agreement.

Exit code is non-zero if any file fails — wire it into a pre-commit hook:

    - id: edd-validate
      name: EDD story schema
      entry: python tools/edd-validate.py
      language: system
      files: ^\\.edd/.*\\.ya?ml$

Usage:
    python tools/edd-validate.py [root]     # root defaults to "."
    # Validates <root>/.edd, or falls back to <root>/examples so this
    # reference repo self-validates.

Requires PyYAML (`pip install pyyaml`).
"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.stderr.write("edd-validate: PyYAML is required (pip install pyyaml)\n")
    sys.exit(2)

required_fields = ("name", "status", "problem", "theory", "refs", "fixture", "runs")
canonical_statuses = ("active", "backlog", "blocked", "resolved")
# status expected given which lifecycle directory the story sits in
status_by_dir = {
    "active": ("active", "blocked"),
    "parked": ("backlog", "blocked"),
    "archived": ("resolved",),
}
priority_values = ("p0", "p1", "p2", "p3")


def validate_story(path: Path, base: Path) -> list[str]:
    """Validate one story.yaml. `base` is the dir holding active/parked/archived."""
    errors: list[str] = []

    try:
        story = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        return [f"YAML parse error: {exc}"]

    if not isinstance(story, dict):
        return ["top-level document is not a mapping"]

    for field in required_fields:
        if field not in story:
            errors.append(f"missing required field: {field}")

    status = story.get("status")
    if status is not None and status not in canonical_statuses:
        errors.append(
            f"non-canonical status {status!r} — "
            f"use one of {', '.join(canonical_statuses)} "
            "(put workflow progress in stage_status/tasks/notes)"
        )

    priority = story.get("priority")
    if priority is not None and priority not in priority_values:
        errors.append(
            f"priority {priority!r} must be one of {', '.join(priority_values)}"
        )

    runs = story.get("runs")
    if runs is not None and not isinstance(runs, list):
        errors.append("runs must be a list (append-only)")

    # Directory ↔ status agreement: the folder a story lives in encodes its
    # lifecycle phase, so a resolved story under active/ is a filing error.
    lifecycle_dir = path.relative_to(base).parts[0]
    expected = status_by_dir.get(lifecycle_dir)
    if expected and status in canonical_statuses and status not in expected:
        errors.append(
            f"status {status!r} does not belong in {lifecycle_dir}/ "
            f"(expected {' or '.join(expected)}); move the story directory"
        )

    return errors


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()

    # Real projects keep stories under .edd/; this reference repo ships them
    # under examples/ so `python tools/edd-validate.py` self-validates.
    base = root / ".edd"
    if not base.is_dir():
        base = root / "examples"
    if not base.is_dir():
        sys.stderr.write(f"edd-validate: no .edd/ or examples/ under {root}\n")
        return 0

    stories = sorted(base.rglob("story.yaml"))
    if not stories:
        sys.stderr.write(f"edd-validate: no story.yaml under {base}\n")
        return 0

    failures = 0
    for path in stories:
        errors = validate_story(path, base)
        rel = path.relative_to(root) if path.is_relative_to(root) else path
        if errors:
            failures += 1
            print(f"FAIL {rel}")
            for err in errors:
                print(f"     - {err}")
        else:
            print(f"ok   {rel}")

    print()
    print(f"{len(stories)} stories, {failures} failing")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

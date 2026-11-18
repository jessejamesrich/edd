#!/usr/bin/env python3
"""Validate EDD story files.

Sweeps `.edd/**/story.yaml`, parses each with a safe loader, and checks the
story schema: required fields, canonical `status`, priority format, acceptance
criteria, and directory <-> status agreement. Against git it also checks the
two things a schema cannot see — that `runs` is still append-only, and that no
acceptance criterion has been reworded since HEAD.

Exit code is non-zero if any file fails, or if there was nothing to measure --
wire it into a pre-commit hook:

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

import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.stderr.write("edd-validate: PyYAML is required (pip install pyyaml)\n")
    sys.exit(2)

required_fields = ("name", "status", "problem", "theory", "refs", "fixture", "runs")

# FIVE WORDS, AND NOTHING ELSE. Two terminal words are not enough: work that
# was examined and declined is `rejected`, not `resolved`, and calling it
# resolved claims work that never happened. Synonyms are what break this --
# `closed`, `done`, `archived` and `merged` all mean resolved to a human and
# nothing to `grep`, and a terminal value nothing greps for is a story nobody
# finds.
canonical_statuses = ("active", "resolved", "rejected", "superseded", "parked")

# The directory a story sits in encodes its lifecycle phase, so a resolved
# story under active/ is a filing error. All three terminal words archive.
status_by_dir = {
    "active": ("active",),
    "parked": ("parked",),
    "archived": ("resolved", "rejected", "superseded"),
}

priority_values = ("p0", "p1", "p2", "p3")

signature_length = 80


def run_entries(text: str) -> list[str]:
    """Every entry under `runs:`, as flat text.

    An entry runs from a `  - ` marker to the next marker or the next
    top-level key. This needs no YAML parser and no heuristic, which matters
    because the mistake it exists to catch produces a file that still parses.
    """
    entries: list[str] = []
    current: list[str] | None = None
    in_runs = False

    for line in text.splitlines():
        if not in_runs:
            if line.rstrip() == "runs:":
                in_runs = True
            continue
        if line and not line[0].isspace():  # next top-level key
            break
        if line.startswith("  - "):
            if current is not None:
                entries.append(" ".join(current))
            current = [line[4:].strip()]
        elif current is not None:
            current.append(line.strip())

    if current is not None:
        entries.append(" ".join(current))
    return [e for e in entries if e]


def signature(entry: str) -> str:
    return entry[:signature_length]


def git_show(repo: Path, relative: str) -> str | None:
    result = subprocess.run(
        ["git", "show", f"HEAD:{relative}"],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    return result.stdout if result.returncode == 0 else None


def head_story_index(repo: Path) -> dict[str, str]:
    """Story paths at HEAD, keyed by DIRECTORY NAME.

    A close moves the directory, so `git show HEAD:<new path>` finds nothing on
    exactly the commit most likely to touch `runs` at the same time. The
    directory name is the story's identity and does not move with the tree.
    """
    result = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", "HEAD"],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return {}
    index: dict[str, str] = {}
    for path in result.stdout.splitlines():
        if path.endswith("/story.yaml"):
            index[path.split("/")[-2]] = path
    return index


def append_only_errors(path: Path, repo: Path, index: dict[str, str]) -> list[str]:
    """Every run entry at HEAD must still BEGIN an entry in the working tree.

    This is the only check that catches a prepend which reused the next
    entry's `- >-` marker: the new text takes the marker, the old entry becomes
    its continuation lines, two entries silently become one, and the entry
    count is UNCHANGED -- so counting entries is blind to it.

    The cost is that rewording an old entry's first 80 characters fails. That
    is deliberate. Runs are append-only history, and a reworded opening and a
    deleted entry are the same characters.
    """
    try:
        relative = str(path.relative_to(repo))
    except ValueError:
        return []

    committed = git_show(repo, relative)
    if committed is None:
        at_head = index.get(path.parent.name)
        committed = git_show(repo, at_head) if at_head else None
    if committed is None:
        return []  # a story that is new at this commit has no history to lose

    working = path.read_text(encoding="utf-8")
    after = run_entries(working)
    openings = {signature(e) for e in after}
    all_of_it = "\n".join(after)

    errors: list[str] = []
    for entry in run_entries(committed):
        opening = signature(entry)
        if opening in openings:
            continue
        shown = opening[:60]
        if opening in all_of_it:
            errors.append(
                f'a run entry was SWALLOWED -- "{shown}..." is still in the '
                "file but now sits inside another entry. Prepend by inserting "
                "a COMPLETE list item after the `runs:` line rather than by "
                "replacing the `  - >-` that follows it"
            )
        else:
            errors.append(
                f'a run entry is GONE -- "{shown}..." opened a run at HEAD and '
                "opens nothing now. Runs are append-only; restore it, and if "
                "the opening was reworded, put the original wording back"
            )
    return errors


def acceptance_errors(story: dict) -> list[str]:
    """Acceptance criteria are shaped so that closing is a CHECK, not a mood.

    Each criterion carries the condition and the thing that decides it. A
    criterion with no `check` is a wish: it reads like a standard and settles
    nothing, and a story full of them closes on whoever is tired first.

    `met` cites the evidence rather than ticking a box, because "met: true"
    and "met: the 2026-11-17 run, 45 passed" cost the same to write and only
    one of them can be checked by the next reader.
    """
    criteria = story.get("acceptance_criteria")
    if criteria is None:
        return []

    if not isinstance(criteria, list):
        return ["acceptance_criteria must be a list, one mapping per criterion"]

    errors: list[str] = []
    seen: dict[str, int] = {}
    for i, item in enumerate(criteria, start=1):
        where = f"acceptance_criteria[{i}]"
        if not isinstance(item, dict):
            errors.append(f"{where} must be a mapping with must/check, not a bare string")
            continue
        must = item.get("must")
        if not isinstance(must, str) or not must.strip():
            errors.append(f"{where} needs a non-empty `must`: the condition, in one line")
        else:
            # TWO CRITERIA WITH THE SAME TEXT cannot be told apart by the drift
            # check below, so one of them can go missing without a word.
            first = seen.setdefault(must.strip(), i)
            if first != i:
                errors.append(
                    f"{where} repeats the `must` of acceptance_criteria[{first}] "
                    "verbatim -- give them different wording or merge them"
                )
        check = item.get("check")
        if not isinstance(check, str) or not check.strip():
            errors.append(
                f"{where} needs a `check`: the command, file or query that decides "
                "it. A criterion nothing can decide is a wish, not a criterion"
            )

    # THE CLOSURE GATE. `rejected` and `superseded` make no claim that the work
    # happened, and `parked` is paused rather than finished -- only `resolved`
    # says it was done, so only `resolved` has to show it.
    if story.get("status") == "resolved":
        unmet = [
            str(item.get("must", f"#{i}"))[:60]
            for i, item in enumerate(criteria, start=1)
            if isinstance(item, dict)
            and not (isinstance(item.get("met"), str) and item["met"].strip())
        ]
        for text in unmet:
            errors.append(
                f'resolved with an unmet criterion -- "{text}" has no `met`. '
                "Either cite what proved it, or close as rejected/superseded"
            )
    return errors


def acceptance_drift_errors(
    path: Path, repo: Path, index: dict[str, str]
) -> list[str]:
    """Every criterion at HEAD must still be present VERBATIM.

    This is the drift the other checks cannot see: not a measurement that
    aged, but a STANDARD that moved. A story whose criteria can be reworded
    while it is open always meets them in the end, and the rewrite leaves no
    trace -- the count is level, every criterion has a `check`, and the diff
    is one line in a file nobody reads twice.

    Narrowing a criterion is the common shape, not deleting one: "every
    tenant's pages" becomes "the tenant we tested". So the comparison is on
    the exact text, and a criterion that genuinely has to change is a NEW
    entry plus a run saying why the old one was wrong.
    """
    try:
        relative = str(path.relative_to(repo))
    except ValueError:
        return []

    committed = git_show(repo, relative)
    if committed is None:
        at_head = index.get(path.parent.name)
        committed = git_show(repo, at_head) if at_head else None
    if committed is None:
        return []  # new at this commit: no standard to move

    try:
        before = yaml.safe_load(committed)
        after = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError:
        return []  # the parse error is reported by validate_story

    musts = lambda doc: [
        item["must"].strip()
        for item in (
            (doc or {}).get("acceptance_criteria") or []
            if isinstance(doc, dict)
            else []
        )
        if isinstance(item, dict) and isinstance(item.get("must"), str)
    ]

    now = set(musts(after))
    errors: list[str] = []
    for text in musts(before):
        if text not in now:
            errors.append(
                f'an acceptance criterion MOVED -- "{text[:60]}..." was a '
                "criterion at HEAD and is not one now. Criteria are the "
                "standard the story is judged against; add a new one and say "
                "in a run why the old one was wrong, rather than editing it"
            )
    return errors


def validate_story(path: Path, base: Path) -> list[str]:
    """Validate one story.yaml. `base` is the dir holding active/parked/archived."""
    errors: list[str] = []

    # THE CHEAPEST CHECK COMES FIRST. A parser answers the question a line
    # scanner cannot -- is this a document -- and answers with a line and a
    # column. A plain scalar containing ": " is a mapping, so a story can stop
    # being YAML while formatters reflow it as text and nothing objects. Every
    # finding below this one is noise if the file is not a document.
    try:
        story = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        return [f"YAML parse error: {exc}"]

    if not isinstance(story, dict):
        kind = "a list" if isinstance(story, list) else type(story).__name__
        return [f"top-level document parses to {kind}, not a mapping"]

    for field in required_fields:
        if field not in story:
            errors.append(f"missing required field: {field}")

    status = story.get("status")
    if status is not None and status not in canonical_statuses:
        errors.append(
            f"non-canonical status {status!r} -- "
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

    errors += acceptance_errors(story)

    lifecycle_dir = path.relative_to(base).parts[0]
    expected = status_by_dir.get(lifecycle_dir)
    if expected and status in canonical_statuses and status not in expected:
        errors.append(
            f"status {status!r} does not belong in {lifecycle_dir}/ "
            f"(expected {' or '.join(expected)}); move the story directory"
        )

    return errors


def repo_root(start: Path) -> Path | None:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=start,
        capture_output=True,
        text=True,
    )
    return Path(result.stdout.strip()) if result.returncode == 0 else None


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()

    # Real projects keep stories under .edd/; this reference repo ships them
    # under examples/ so `python tools/edd-validate.py` self-validates.
    base = root / ".edd"
    if not base.is_dir():
        base = root / "examples"

    # FAIL CLOSED ON ABSENCE. A gate that measures nothing must not pass: a
    # renamed directory, a bad argument or a sweep that matched no files all
    # produce green here, which is the shape of a check that cannot fail.
    if not base.is_dir():
        sys.stderr.write(f"edd-validate: no .edd/ or examples/ under {root}\n")
        return 1

    stories = sorted(base.rglob("story.yaml"))
    if not stories:
        sys.stderr.write(f"edd-validate: no story.yaml under {base}\n")
        return 1

    repo = repo_root(root)
    index = head_story_index(repo) if repo else {}

    failures = 0
    for path in stories:
        errors = validate_story(path, base)
        if repo:
            errors += append_only_errors(path, repo, index)
            errors += acceptance_drift_errors(path, repo, index)
        rel = path.relative_to(root) if path.is_relative_to(root) else path
        if errors:
            failures += 1
            print(f"FAIL {rel}")
            for err in errors:
                print(f"     - {err}")
        else:
            print(f"ok   {rel}")

    print()
    history = "against HEAD" if repo else "no git repo, history not checked"
    print(f"{len(stories)} stories, {failures} failing ({history})")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

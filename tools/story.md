# Create EDD Story

Create a new Evaluation-Driven Development story for tracking an investigation.

Drop this into your agent tooling as a slash command (e.g. Claude Code
`.claude/commands/story.md`, or the equivalent for your setup) so "new story"
scaffolds a well-formed `story.yaml`.

## What to do

First, check whether this story emerged from a previous one. Read active and
recently resolved stories:

```bash
grep -rl "status: active\|status: resolved" .edd/*/*/story.yaml
```

If the user says something like "the fix for X worked but now Y is broken," this
is a **split** — the previous story should be resolved (moved to
`.edd/archived/`) and this new one links back via `emerged_from`.

Then ask the user the following, one at a time. Wait for each answer.

1. **What's the problem?** (1–3 sentences: what's wrong, or what you're trying to
   improve.)
2. **What's your initial theory?** (Best guess at why. "Not sure yet" is fine.)
3. **What fixture or test proves/disproves this?** (An existing fixture file, a
   command to run, or "need to create one.")
4. **Give it a short slug.** (e.g. `chat-grounding-drift`, `copy-architecture`,
   `timeline-binding`.)
5. **What priority?** (`p0` do now, `p1` do next, `p2` do soon, `p3` lowest.
   `p3` is not a parking space — parked is `status: parked`.
   Default `p2`.)
6. **Any LLM model / thinking config to track?** (Optional — only for stories
   that investigate LLM behavior.)

## After collecting answers

1. Create the directory: `.edd/active/<slug>/`
2. Create `story.yaml`:

```yaml
name: <descriptive name>
status: active
priority: <p0|p1|p2|p3>
created: <today's date, ISO 8601>
emerged_from: <parent-slug or omit if none>

problem: >
  <problem description>

theory: >
  <initial theory>

refs: []

fixture: |
  <fixture file path or command>

# Include model_config only for stories that investigate LLM behavior
model_config:
  thinking: <low|medium|high>
  tasks:
    <task-name>: <model>

runs: []
```

3. If this emerged from a resolved story: set the parent's `status: resolved`,
   move the parent directory to `.edd/archived/<parent-slug>/`, and add a
   `resolved_by` note pointing at the final run that confirmed the fix.
4. If the user referenced an existing fixture, note it. If they need a new one,
   help create it.
5. Tell the user:
   - Story created at `.edd/active/<slug>/story.yaml`
   - The loop: observe → annotate → hypothesize → experiment → measure
   - After each run, append an entry to `runs:` — prose opening with a date,
     at the end of the list, written as a folded scalar
   - Update `theory:` as understanding evolves
   - When a fix works but creates a new problem: resolve this story, start a new
     one with `emerged_from`.

# Create EDD Story

Open a new Evaluation-Driven Development story: the card you create when
somebody says "here is what we need to do". The work may be a build or an
investigation, and the card is the same either way.

`skills/opening-an-edd/` is the procedure, including how to write an acceptance
criterion that can actually settle the question. This file is the interactive
scaffold.

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

1. **What needs doing, or what's wrong?** (1–3 sentences. A defect or the work
   itself; "the new-post page is a tab bar with nothing in it" is a problem.)
2. **What would make this finished?** Take them one at a time until they run
   out, and for each one ask **who or what decides it** — a command, or a
   person by name. These become `acceptance_criteria`, and they are the part of
   the card that matters. Write them now, before any work: criteria written
   afterwards describe what got built, which is the failure the field exists to
   prevent.
3. **Give it a short slug.** (Three to six words, hyphenated, naming the
   problem rather than the fix: `citation-panel-for-answers`, not
   `add-citation-panel`.)
4. **What priority?** (`p0` do now, `p1` do next, `p2` do soon, `p3` lowest.
   `p3` is not a parking space — parked is `status: parked`.
   Default `p2`.)
5. **Is there a fixture?** (A file, a command, or how a person checks it. "I
   look at the page" is an answer.)
6. **Do you have a theory?** Ask only if the card is about why something
   behaves the way it does. On work-to-do, skip it — a theory there is the
   problem written twice, and the field is optional.
7. **Any LLM model / thinking config to track?** (Optional — only for stories
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
  <what isn't settled: the defect, or the work>

# theory is OPTIONAL. Include it only when the cause is unknown; on a card
# that opens as work to do it restates the problem.

refs: []

fixture: |
  <a file, a command, or how a person checks it>

acceptance_criteria:
  - must: <one condition, not three>
    check: <the command, or what the person does>
    by: <ci, or the person's name>

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
   - Sign a criterion off with `met` citing the evidence, `met_by` for who did
     the work, and `feedback` for what the reviewer said. Review usually
     produces more criteria than it closes: write the new finding as a NEW
     criterion rather than rewording the old one
   - Criteria and feedback are compared against HEAD and cannot be edited. When
     a bar turns out to be wrong, add a new criterion and say why in a run
   - `resolved` needs `met` on every criterion. If it cannot be met, the honest
     exits are `rejected` and `superseded`
   - Update `theory:` as understanding evolves, if the card has one
   - When a fix works but creates a new problem: resolve this story, start a new
     one with `emerged_from`.

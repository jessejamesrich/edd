# Evaluation-Driven Development (EDD)

A lightweight methodology for **work whose shape isn't settled when you start
it** — AI generation, retrieval, agents and classifiers, where "quality" is a
spectrum rather than a boolean, and equally the build where nobody yet agrees
what done means. One story is one unit of work: the card you open when you say
"here is what we need to do", carrying the conditions for calling it finished
and the record of every attempt.

EDD is **context as files.** Every piece of work lives as a small YAML document
in your repo, versioned alongside the code. The primary reader isn't a
dashboard — it's the **next agent (or human) to pick up the work.** They read
the story and know exactly where things stand without digging through hundreds
of lines of chat history or scrollback.

> **Pairs with [ghostbus](https://github.com/jessejamesrich/ghostbus).**
> ghostbus is the *live wire* — a tmux-backed bus for real-time coordination
> between multiple local coding agents. EDD is the *durable record* — the
> file-based memory that outlives any single session. Bus for now, files for
> memory. Neither depends on the other; they just compose well.

## In production

edd runs a client data project at OMTM.ai: 99 stories and about 2,000 logged
runs between September and November 2026, covering ingestion from ten source
systems, a read-only access audit, dataset anonymization and a training proof
of concept. Numbers the project reports to the client are backed by executable
checks that recompute them from raw data.

## Why

Traditional tests say pass/fail. That's the right tool for deterministic code:
a function returns the wrong bucket → fix → test → done.

But when you're tuning a generator, a retrieval pipeline, or an agent, the
output is non-deterministic and quality is a gradient. "Did it pass?" is the
wrong question. The right questions are **how good, why, and what changed since
last time?** A green checkmark can't hold a hypothesis, a run history, or the
reason you tried the thing you tried.

EDD gives that state a home: a mutable **story** that names the work, holds the
conditions for finishing it, and accumulates an append-only list of **runs**.
It's deliberately low-ceremony — plain YAML, plain directories, greppable, no
service to stand up.

The same shape turned out to fit work that is not a tuning problem at all.
Building infrastructure nobody has specified, settling what a word in your
domain means, getting a listing out of a web form and into the repo: in each
one the question "is it done?" has an answer somebody has to decide, and the
reason you tried what you tried is worth keeping. A story is a card you can
hand to the next session, so this repo's stories are cards more often than they
are investigations.

## Concepts

### Story

A mutable working document that names the work, holds the conditions for
calling it finished, and lists runs. The story is the entry point to ongoing
work, and the unit you open when you decide to do something.

- Active stories live in `.edd/active/<slug>/story.yaml`
- Parked stories live in `.edd/parked/<slug>/story.yaml`
- Resolved stories live in `.edd/archived/<slug>/story.yaml`

A story has:

- **name** — human-readable title
- **status** — one of `active`, `resolved`, `rejected`, `superseded`, `parked`
- **problem** — what isn't settled, in 1–3 sentences. A defect, or the work
  itself: "the new-post page is a tab bar with nothing in it" is as good a
  problem as a 500
- **refs** — loose association to branches, commits, docs
- **fixture** — how to reproduce / test (a command, a file reference, or a
  description)
- **runs** — append-only list of results, newest or oldest first but
  consistently one or the other

Common optional fields:

- **priority** — `p0` immediate, `p1` what makes the product wrong or broken,
  `p2` real and worth doing with nothing visibly broken, `p3` lowest.
  **`p3` is not a parking space.** Say parked once, with `status`, or the day
  comes when a story is parked by one signal and open by the other
- **theory** — hypothesis about *why*, and what fix to try. Wanted whenever the
  cause is unknown, and left out of a card that opens as work to do rather than
  a question, where a theory is the problem statement written twice
- **depends_on** — story that should resolve before this one starts
- **blocked_by** — the immediate blocker. A blocked story's `status` stays
  `active` or `parked`; blocking is a fact about the work, not a phase of it
- **emerged_from** — the previous story that exposed this new failure mode
- **continues** / **continued_by** — forward chain to the next story
- **acceptance_criteria** — the conditions for closing, one per entry, each
  with the thing that decides it. See *Acceptance criteria* below
- **notes** — short current-truth context that doesn't belong in run history
- **model_config** — for stories that investigate LLM behavior: record the
  task → model mapping and thinking level, so future runs compare against a
  known configuration

The story is mutable. The theory can change as you learn. The problem can
sharpen. Refs accumulate. That's fine — **the story is current truth, not
history.** (History lives in `runs`.)

#### Canonical status meanings

- `active` — open and intended for current / near-current execution.
- `resolved` — the work was done.
- `rejected` — examined and deliberately NOT done. **This is why two terminal
  words are not enough.** Work that was considered and declined is not
  resolved, and calling it resolved claims work that never happened — in one
  real archive, 23 of 425 closed stories are this.
- `superseded` — the question moved to another story, which the body names.
- `parked` — scheduled against nothing.

`resolved`, `rejected` and `superseded` all move the whole story directory to
`.edd/archived/<slug>/`; `parked` moves it to `.edd/parked/<slug>/`. The
directory and the status say the same thing, and the validator checks that they
agree.

**Pick the vocabulary once and let nothing else in.** This list was four words
for a while, with `backlog` and `blocked` among them and `rejected` missing.
Nine synonyms accumulated — `closed`, `done`, `archived`, `merged` — because
nothing refused them, and a quarter of one archive became invisible to
`grep "status: resolved"`, which is how the next session reads recent history.
A terminal value nothing greps for is a story nobody finds.

Do **not** use `in_progress`, `stage-a-landed`, `completed`, or other custom
workflow labels as `status`. Capture phase progress in fields like
`stage_status`, `tasks`, `runs`, or `notes`, and keep `status` canonical. This
keeps the "what's open?" query trivial and stable.

#### Pointers rot quietly

`fixture` and `refs` are how the next session reaches the work, and nothing
announces it when they stop resolving. The story still parses, still has a
theory, still reads as current truth, and the one thing it tells you to run is
gone. The shape in the wild is a reference that was exact when written — a doc
naming `welcome-mcp/guide.ts:282` after that route was deleted — so the
validator resolves path-shaped `fixture` and `refs` entries against the repo.

Only paths are checked, and only for a real project's `.edd/`. A token counts
as a path when it carries a directory separator and a short extension, which
leaves branch names like `fix/issue-123`, bare commit shas, URLs and numbers
like `0.96` alone. A reference that is genuinely gone is a run entry saying so,
not a silent deletion.

#### Acceptance criteria

The story is mutable on purpose — the theory changes, the problem sharpens,
refs accumulate. Acceptance criteria are the one part that must not, because
they are what the story is judged against:

```yaml
acceptance_criteria:
  - must: contradiction-set grounding at or above 0.9, from a baseline of 0.74
    check: evals/grounding/run.py evals/grounding/contradiction-set.jsonl
    by: ci
    met: the 2026-01-14 run, 0.91
  - must: every claim-bearing sentence links to the passage it came from
    check: open an answer in the console, click through each link
    by: jesse
    met: 2026-01-20, checked on six answers
    met_by: the agent built the panel, jesse checked it
    feedback: >
      The links work. A sentence drawing on two passages shows only the first.
  - must: no regression on the plain-QA set, currently 0.96
    check: evals/grounding/run.py evals/grounding/plain-qa.jsonl
    by: ci
```

**An array, not a paragraph.** Prose bundles conditions — "zero repeated
openers, ≥ 3 cross-section references, rating ≥ 4.0" is three standards in one
sentence, and a story meeting two of them reads as met at a glance. Separate
entries can be satisfied separately, and the unsatisfied one stays visible.

**A check is a person as often as a command.** Plenty of work is finished when
somebody looks at it and says so, and no runner reports on whether a palette
reads as one system. `check` is free text for that reason: "open the builder and
compare against the spec" is a check. What matters is that it names something
that can actually settle the question.

**`by` is who decides, `met_by` is who did the work.** A card waiting on a
person and a card waiting on CI are different kinds of open, and the difference
is worth a grep when you are deciding what to pick up. They are also separate
facts: the ordinary case is an agent building and a person approving, and
collapsing them loses which of the two to go back to. `met_by` without `met`
is refused, because naming who approved something reads as closed in every
listing that greps for `met`.

**Feedback belongs on the criterion, and it is somebody's words.** Review
rarely arrives as a verdict. It arrives as "the links work, but a sentence
drawing on two passages shows only the first", which is one criterion signed
off and one more discovered. Write the first as `met` with the comment in
`feedback`, and the second as a new criterion rather than a note on the old
one. The validator compares `feedback` against HEAD and refuses a rewrite: an
agent handed "the excerpt should inherit from the body" can otherwise satisfy
the criterion by softening the sentence that asked for it, and the card then
closes against feedback nobody gave. Adding a later round is fine, since that
appends.

**Each criterion carries what decides it.** A `must` with no `check` is a
wish: it reads like a standard and settles nothing, so the story closes on
whoever is tired first. `met` cites the evidence rather than ticking a box —
`met: true` and `met: the 2026-01-14 run, 0.91` cost the same to write and
only one of them can be checked by the next reader.

**The standard cannot move while the work is open.** This is the drift the
rest of the format cannot see. A run entry that ages is visible, because it
carries its date; a criterion reworded mid-story leaves no trace at all. The
count stays level, every entry still has a `check`, and the diff is one line
in a file nobody reads twice. The usual shape is narrowing rather than
deletion — "every tenant's pages" becomes "the tenant we tested" — and the
story then closes honestly against a standard it would have failed. So the
validator compares criteria against HEAD on exact text, and a criterion that
genuinely has to change is a NEW entry plus a run saying why the old one was
wrong. Moving a goalpost is a finding about the work, not an edit.

**A `met` that names a date names a run.** `met` is free text so it can carry
a number, but a date in it is a claim about this story's own history, and a
`met` citing a run the story does not hold is decoration — usually a date
typed from memory that landed a day off. A `met` with no date is left alone:
it may cite a commit or a person, and a check that cannot decide should not
pretend to.

**Only `resolved` has to show its work.** `rejected` and `superseded` make no
claim that the work happened, and `parked` is paused rather than finished, so
the validator requires a `met` on every criterion for `resolved` alone. A
story that cannot meet its criteria has two honest exits, and both are already
in the vocabulary.

Keep `.edd/active` small — only stories an agent may reasonably pick up *now*.
Move parked stories to `.edd/parked`.

### Run

An entry in the story's `runs` list: prose that opens with a date and says its
finding in the first clause.

```yaml
runs:
  - >
    2026-03-04 THE PASSAGES WERE LAST IN THE PROMPT, not under-retrieved.
    Moving them above the instruction block took invented facts from 1 in 4
    questions to 1 in 30 with no prompt wording change, so H2 holds and H1 was
    never the cause.
```

**Start with a one-liner if that is all the run earned, and do not formalise
it.** One real archive began with a `PASS|FAIL <id>` template and ended up with
it on 77 of 2434 entries: the shape came from fixture loops, where a run really
is one artifact with a verdict, and most stories are not fixture loops. A
verdict cannot carry what was measured, so the entries grew into prose and the
documentation stayed where it was for months. If your runs are fixture verdicts,
a verdict is the right entry. If they are findings, write the finding.

Open with the date so the entry is self-dating, and put the finding first — the
next reader scans openings, not bodies.

**The one-line format discarded its own payload, which is the real reason it
died.** In YAML a space-hash opens a comment:

```yaml
runs:
  - 2026-01-02T14:10 FAIL throughline-set # 9/12 pages repeated an opener
```

parses to exactly `"2026-01-02T14:10 FAIL throughline-set"`. The measurement
after the hash reaches no parser, no `grep` over loaded YAML, and no agent that
reads the story as a document — only a human looking at the raw file. So the
template recorded the verdict and threw away the finding, silently, because the
file parses and the text is right there on screen. In one archive, 59 entries
across 17 stories lose 11,844 characters that way. A folded scalar keeps the
hash as text.

**Append at one end and keep to it.** Oldest-first is the easier default,
because the newest entry lands where nothing can be damaged. In one archive 156
stories ran oldest-first and 28 newest-first, so read a story's last two dates
before you add to it rather than assuming.

Runs are **append-only. Never edit or delete a run entry.** The run list *is*
the regression history. A hypothesis that turned out wrong isn't a mistake to
erase — it's a data point the next run builds on. **If an old entry was wrong,
append a correction that names the error.**

#### Two ways an entry destroys its neighbour in silence

Both are YAML facts rather than EDD rules, and both pass every gate that is not
looking for them.

**A prepend that reuses the next entry's marker.** Inserting text by replacing
`runs:\n  - >-\n` gives the new entry that marker and turns the old one into
its continuation lines. Two entries become one, the document still parses, and
the entry count does not drop — so counting entries cannot detect it. Insert a
**complete list item**, marker and all, or append at the end.

**A colon-space in a plain scalar.** `": "` is YAML's mapping separator, and
what it costs depends on where it sits:

```yaml
problem: the field is email: { template }   # FAILS to parse — "mapping values
                                            # are not allowed here". Loud.
runs:
  - 2026-03-04 the locales kept: en and fr  # PARSES, as a mapping. The entry
                                            # is a dict where every reader
                                            # expects a string, and the run
                                            # count is unchanged. Silent.
  - >
    2026-03-04 the locales kept: en and fr  # fine — a folded scalar is immune
```

A field value breaks noisily; a run entry breaks quietly, which is the one that
survives. **Write runs as folded scalars** and it cannot happen. Formatters
reflow what they cannot parse as though it were text, so neither case announces
itself, and a sweep of one 452-story archive found 126 entries across 23
stories whose prose had been cut at its first `": "` years earlier.

Parse the file, and check the entries are strings — but only flag the exact
shape, since a mapping run entry can be deliberate:

```bash
python3 -c "
import re, sys, yaml
d = yaml.safe_load(open(sys.argv[1]))
print([i for i, r in enumerate(d['runs'])
       if isinstance(r, dict) and len(r) == 1
       and not re.fullmatch(r'\d{4}-\d{2}-\d{2}\S*', str(list(r)[0]))] or 'clean')
" .edd/active/<slug>/story.yaml
```

### Run detail file (optional)

When a run needs deeper analysis, create an immutable run file:

```
.edd/active/<slug>/runs/YYYY-MM-DD-<id>.yaml
```

Most runs don't need one — the one-liner in the story is enough. Only expand
when the diagnosis matters for future reference:

```yaml
id: <run-id>
date: YYYY-MM-DDTHH:MM
commit: <sha>
result: pass|fail
failed_at: <stage-name>          # which stage of your pipeline broke

observe:
  quality_score: 88              # whatever signal you measure
  <metric>: <value>

annotate: >
  What actually happened, in one or two sentences.

hypothesize: >
  Why you think it happened, and what layer owns the fix.

fix_targets:
  - path/to/the/file/you/think/is/responsible
```

Never edit a run file after creation. If the hypothesis was wrong, that shows
up in the next run — and that's useful information, not a mistake.

## Story lifecycle

A story resolves when its hypothesis is confirmed — **even if the fix creates
new problems.** New problems caused by a successful fix are *new stories*.

At each run, ask: **did my fix work for what it was supposed to fix?**

- **Yes, but something else broke** → resolve this story, create a new one with
  `emerged_from` pointing back.
- **No, my hypothesis was wrong** → update the theory, keep going.
- **Partially** → update the theory, keep going.

The `emerged_from` field links the causal chain:

```
copy-architecture          status: resolved
  └→ adjacent-surfaces     status: resolved, emerged_from: copy-architecture
      └→ base-copy-leak     status: active,   emerged_from: adjacent-surfaces
```

An agent reads the active story and follows `emerged_from` backwards *only if*
it needs to understand how we got here. Usually it won't — the active story's
problem and theory are self-contained.

### Story vs. run annotation

Stories are for **recurring failure modes or hypotheses.** Symptoms and one-off
bugs are run annotations.

| Signal                                          | Story or annotation?                        |
| ----------------------------------------------- | ------------------------------------------- |
| Section-heading ownership leaks across stages   | **Story** — recurring failure mode          |
| Intent keeps drifting into the wrong content    | **Story** — recurring hypothesis            |
| Duplicate header on output X                    | Annotation — a symptom in a run             |
| One block failed to render                      | Annotation — a symptom in a run             |
| Upstream 429 timeout                            | Annotation — infra noise (unless it recurs) |

If you're not sure, start with a run annotation. If it recurs across 3+ runs,
promote it to a story.

## The loop

1. **Open a story** when work starts that outlives this session, and write
   the acceptance criteria before the work rather than after.
2. **Run the fixture** — whatever reproduces the behavior (a script, an eval, a
   manual call).
3. **Observe** — read the output, scores, logs.
4. **Annotate** — what failed, and where? Add a run line to the story.
5. **Hypothesize** — update the `theory`, on a story that has one. What's
   wrong, and what layer owns the fix?
6. **Experiment** — make the code / prompt change.
7. **Measure** — run the fixture again. Add another run line.
8. **Repeat** until the story reaches `status: resolved`.

## Multi-phase stories (ports, migrations, planned restorations)

Some stories aren't one observe→measure cycle — they're an N-phase,
dependency-ordered execution plan (port a large module to another language,
migrate a service, restore a broken pipeline). For these, runs aren't
observations — they're **execution steps**, each landing one phase.

The rule, non-negotiable: **commit the EDD update in the same turn the phase
lands.** Concretely, the per-phase loop is:

1. Write / edit the code for phase N.
2. `git commit` the code change (`feat(scope): phase N/M — <description>`).
3. Immediately, in the same turn:
   - Append a one-line `runs:` entry with the phase SHA + a terse description of
     what landed and what's stubbed.
   - Remove the entry from `phases_remaining:` (or your remaining-work list).
   - `git commit` the EDD change as a separate `docs(edd): backfill phase-N SHA`
     commit.

Only then move to phase N+1.

**Why two commits per phase** instead of one squashed commit: the EDD entry
references the phase SHA, but that SHA only exists *after* the phase commit
lands. Bundling them by amending produces a SHA-chase cycle — every amend
changes the SHA the EDD references, forcing another amend. Two commits is
annoying once and stable forever.

**Failure mode to watch for:** batching several phases' worth of EDD updates at
the end "for speed" produces a sound `runs:` list but a broken audit trail in
git. The phase commit and its EDD-update commit should sit next to each other in
`git log --oneline`. If phase N's EDD update is adjacent to phase N+3's code
commit, the discipline broke.

## When to use EDD

**Good fit:**

- AI / ML system tuning — generation, retrieval, agents, classifiers, embeddings
- Work where nobody has yet agreed what finished means, so settling the criteria
  is part of the job
- Anything that outlives one session, where the next agent or person needs the
  thread rather than the scrollback
- A build whose verification is somebody looking at it, which no test reports on

**Not needed:**

- Work you finish in one sitting where a passing test is the whole of "done"
- A bug with an obvious cause: fix it, test it, move on

The boundary is not the subsystem. An earlier version of this list named CRUD
routes, UI components and infrastructure as out of scope, and then the stories
that most needed a card were an infrastructure-as-code migration, an App Store
listing and the definition of the word "block". What decides it is whether
"finished" has an answer somebody has to make, and whether anyone has to pick
the work up again later.

EDD **sits above** your existing design docs, specs, and prompts — it doesn't
replace them. A story names the work and points at the relevant contract /
prompt / code. Those artifacts stay the source of truth for *how the system
works*; stories track *what we're changing, what would make it done, and
whether it is.*

## Finding active work

To see what's open, sorted by priority:

```bash
for f in .edd/active/*/story.yaml; do
  slug=$(basename "$(dirname "$f")")
  st=$(grep "^status:" "$f" | head -1 | sed 's/status: //')
  pri=$(grep "^priority:" "$f" | head -1 | sed 's/priority: //' || echo "p?")
  [ "$st" = "active" ] && echo "$pri  $st  $slug"
done | sort
```

An unprioritised story prints `p?` and sorts last, which is a question rather
than a silent filing at the bottom.

Parked, closed, and causal chains:

```bash
grep -rl "status: parked" .edd/parked/*/story.yaml        # parked
grep -rl "status: resolved" .edd/archived/*/story.yaml    # done
grep -rl "status: rejected" .edd/archived/*/story.yaml    # deliberately not done
grep -R "emerged_from" .edd/active .edd/parked .edd/archived  # trace a chain
```

## Layout

```
.edd/
  active/                 # open, pick-up-now stories
    <slug>/
      story.yaml
      runs/               # optional immutable run detail files
  parked/                 # scheduled against nothing
    <slug>/story.yaml
  archived/               # resolved, rejected, superseded
    <slug>/story.yaml
```

This repo ships:

- **[`examples/`](examples/)** — 22 synthetic stories, enough to show the whole
  vocabulary in use rather than one of each. Seven active, two parked, thirteen
  closed: ten `resolved`, two `rejected` (work examined and deliberately not
  done, which is the word most archives are missing), and one `superseded`
  whose body names where the question went. Two causal chains run end to end —
  `retrieval-recall-floor` to `chat-grounding-drift`, and
  `copy-architecture-bridge` to `adjacent-surfaces` to `base-copy-leak` — so
  `emerged_from` can be read forwards and backwards.
  `port-the-pipeline-to-typescript` is a six-phase story whose runs are
  execution steps naming the commit that landed each one.
  `a-cache-key-ignores-the-locale` carries a run detail file.
  `classifier-drifts-after-retraining` carries `model_config`.
  `citation-panel-for-answers` is a card rather than an investigation: no
  theory, criteria split between `ci` and a person, one signed off with the
  feedback that produced the next two. None of them is real; the problems are
  the ordinary ones.
- **[`tools/story.md`](tools/story.md)** — a scaffold prompt for creating a new
  story (drop it in as a slash command / agent command).
- **[`skills/writing-an-edd-run/`](skills/writing-an-edd-run/)** — the
  procedure for the two operations that happen most, appending a run and
  closing a story, as a skill an agent loads when it needs it. The README tells
  you what a run is; this tells you how to write one without destroying the one
  below it. Drop it in wherever your agent reads skills.
- **[`skills/opening-an-edd/`](skills/opening-an-edd/)** — the procedure for
  the operation that starts everything: what belongs on a card that is not an
  investigation, how to write an acceptance criterion that can settle the
  question, and the four ways a criterion is born unable to fail.
- **[`tools/edd-validate.py`](tools/edd-validate.py)** — a dependency-light
  validator: every story parses, `status` is one of the five, the status agrees
  with the directory, every acceptance criterion carries something that decides
  it, `resolved` has a `met` on each one, and — against git — **no run entry
  that existed at HEAD stopped beginning an entry**, which is the only check
  that catches the swallowed prepend above, plus **no criterion or piece of
  feedback reworded since HEAD**, which is the only check that catches a
  goalpost moving. For a real project's `.edd/` it also resolves path-shaped
  `fixture` and `refs` entries. It fails when it finds nothing to measure. Wire
  it into a pre-commit hook.

## License

MIT — see [LICENSE](LICENSE).

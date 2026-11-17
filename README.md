# Evaluation-Driven Development (EDD)

A lightweight methodology for building **non-deterministic systems** — AI
generation, retrieval, agents, classifiers — where "quality" is a spectrum, not
a boolean. Based on the scientific method: **observe, annotate, hypothesize,
experiment, measure.**

EDD is **context as files.** Every investigation lives as a small YAML document
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

EDD gives that state a home: a mutable **story** that names the problem, holds
the current theory, and accumulates an append-only list of **runs**. It's
deliberately low-ceremony — plain YAML, plain directories, greppable, no
service to stand up.

## Concepts

### Story

A mutable working document that names the problem, holds the current theory,
and lists runs. The story is the entry point to ongoing work.

- Active stories live in `.edd/active/<slug>/story.yaml`
- Parked stories live in `.edd/parked/<slug>/story.yaml`
- Resolved stories live in `.edd/archived/<slug>/story.yaml`

A story has:

- **name** — human-readable title
- **status** — one of `active`, `resolved`, `rejected`, `superseded`, `parked`
- **problem** — what's wrong, in 1–3 sentences
- **theory** — current hypothesis about *why*, and what fix to try
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
- **depends_on** — story that should resolve before this one starts
- **blocked_by** — the immediate blocker. A blocked story's `status` stays
  `active` or `parked`; blocking is a fact about the work, not a phase of it
- **emerged_from** — the previous story that exposed this new failure mode
- **continues** / **continued_by** — forward chain to the next story
- **success_criteria** — measurable conditions for resolving the story
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

1. **Create a story** when you start investigating a problem.
2. **Run the fixture** — whatever reproduces the behavior (a script, an eval, a
   manual call).
3. **Observe** — read the output, scores, logs.
4. **Annotate** — what failed, and where? Add a run line to the story.
5. **Hypothesize** — update the `theory`. What's wrong, and what layer owns the
   fix?
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
- Non-deterministic output that needs iterative quality improvement
- Problems where the diagnosis isn't obvious upfront and the fix is a hypothesis

**Not needed:**

- Deterministic bugs (wrong bucket → fix → test → done)
- CRUD routes, UI components, infrastructure
- Anything where a unit test is the complete verification

EDD **sits above** your existing design docs, specs, and prompts — it doesn't
replace them. A story says "we're investigating X" and points at the relevant
contract / prompt / code. Those artifacts stay the source of truth for *how the
system works*; stories track *what we're trying to change and whether it's
working.*

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

- **[`examples/`](examples/)** — 21 synthetic stories, enough to show the whole
  vocabulary in use rather than one of each. Six active, two parked, thirteen
  closed: ten `resolved`, two `rejected` (work examined and deliberately not
  done, which is the word most archives are missing), and one `superseded`
  whose body names where the question went. Two causal chains run end to end —
  `retrieval-recall-floor` to `chat-grounding-drift`, and
  `copy-architecture-bridge` to `adjacent-surfaces` to `base-copy-leak` — so
  `emerged_from` can be read forwards and backwards.
  `port-the-pipeline-to-typescript` is a six-phase story whose runs are
  execution steps naming the commit that landed each one.
  `a-cache-key-ignores-the-locale` carries a run detail file.
  `classifier-drifts-after-retraining` carries `model_config`. None of them is
  real; the problems are the ordinary ones.
- **[`tools/story.md`](tools/story.md)** — a scaffold prompt for creating a new
  story (drop it in as a slash command / agent command).
- **[`skills/writing-an-edd-run/`](skills/writing-an-edd-run/)** — the
  procedure for the two operations that happen most, appending a run and
  closing a story, as a skill an agent loads when it needs it. The README tells
  you what a run is; this tells you how to write one without destroying the one
  below it. Drop it in wherever your agent reads skills.
- **[`tools/edd-validate.py`](tools/edd-validate.py)** — a dependency-light
  validator: every story parses, `status` is one of the five, the status agrees
  with the directory, and — against git — **no run entry that existed at HEAD
  stopped beginning an entry**, which is the only check that catches the
  swallowed prepend above. It fails when it finds nothing to measure. Wire it
  into a pre-commit hook.

## License

MIT — see [LICENSE](LICENSE).

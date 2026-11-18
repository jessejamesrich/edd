---
name: writing-an-edd-run
description: Append a run to an EDD story, or close one. Use whenever you have finished a piece of work an active story covers, are about to write into .edd/, or are about to mark a story resolved, rejected, superseded or parked. Covers the run format, the three ways a run entry destroys its neighbour while every check stays green, what a run is allowed to assert, how to sign off an acceptance criterion and record feedback, and the gate before a close.
---

# Writing an EDD run

One rule, and everything here serves it:

> **A run is history. Append it, never edit it, and let it say only what you
> measured.**

The README is the methodology — what a story is, when to open one, the status
vocabulary. This is the procedure for the operations that happen
most: adding a run, signing off a criterion, and closing a story. Drop this file in as a skill wherever your
agent reads them.

## The format

A run entry is prose that opens with a date and says its finding in the first
clause, written as a folded scalar:

```yaml
runs:
  - >
    2026-02-22 THE TWO COUNTS DISAGREE BY 14% MEAN on the same 80 documents,
    measured by counting each one both ways. On the three code-heavy documents
    the gap is 31%.
```

Open with the date so the entry is self-dating. Put the finding first — the
next reader scans openings, not bodies.

**A verdict is still the right entry when a run really is one artifact with a
verdict.** A fixture loop produces `2026-01-14 PASS contradiction-set at 0.91`
and that is complete. Most stories are not fixture loops, and a verdict cannot
carry what was measured. Write whichever the run earned, and do not formalise a
template for it — one archive did, and ended up with the template on 3% of
2434 entries while the corpus wrote prose anyway.

**Append at one end and keep to it.** Oldest-first is the easier default,
because the newest entry lands where nothing can be damaged. Read a story's
last two dates before adding to it rather than assuming.

## Three ways an entry destroys its neighbour in silence

All three are YAML facts rather than EDD rules, and all three pass every check
that is not looking for them.

**A prepend that reuses the next entry's marker.** Inserting text by replacing
`runs:\n  - >-\n` gives the new entry that marker and turns the old one into
its continuation lines. Two entries become one, the document still parses, and
the entry count does not drop — so counting entries cannot detect it. Insert a
**complete list item**, marker and all, or append at the end.

**A ` #` throws away the rest of the line.** In YAML a space-hash opens a
comment, so

```yaml
  - 2026-01-02 FAIL throughline-set # 9 of 12 pages repeated an opener
```

parses to exactly `"2026-01-02 FAIL throughline-set"`. The measurement reaches
no parser, no `grep` over loaded YAML and no agent reading the story as a
document — only a human looking at the raw file. One archive lost 11,844
characters across 59 entries that way, and nothing reported it, because the
file parses and the text is right there on screen. A folded scalar keeps the
hash as text.

**A `": "` in a plain scalar.** It is YAML's mapping separator, and what it
costs depends on where it sits:

```yaml
problem: the field is email: { template }   # FAILS to parse — "mapping values
                                            # are not allowed here". Loud.
runs:
  - 2026-01-02 the locales kept: en and fr  # PARSES, as a mapping. The entry
                                            # is a dict where every reader
                                            # expects a string, and the run
                                            # count is unchanged. Silent.
  - >
    2026-01-02 the locales kept: en and fr  # fine — a folded scalar is immune
```

A field value breaks noisily; a run entry breaks quietly, which is the one that
survives. In one 452-story archive, 126 entries across 23 stories had been cut
that way years earlier and nobody had noticed.

**Writing runs as folded scalars makes all three impossible.** That is the
whole reason to prefer them.

## Verify what you wrote

```bash
python tools/edd-validate.py
```

It parses every story, checks the status against the directory, and checks
against git that every run entry present at HEAD still BEGINS an entry — which
is the only check that catches the swallowed prepend. Run it before you hand
the story over.

Then confirm no entry became a mapping, and flag only the exact shape, since a
mapping run entry can be deliberate:

```bash
python3 -c "
import re, sys, yaml
d = yaml.safe_load(open(sys.argv[1]))
print([i for i, r in enumerate(d['runs'])
       if isinstance(r, dict) and len(r) == 1
       and not re.fullmatch(r'\d{4}-\d{2}-\d{2}\S*', str(list(r)[0]))] or 'clean')
" .edd/active/<slug>/story.yaml
```

**Not every mapping is damage.** A run may legitimately be `date` plus `note`,
or `at`/`step`/`result`, and in that same archive 218 entries are. The accident
has exactly one shape: a single key that is prose, because YAML cut the
sentence at its first `": "`. Asserting that every run is a string reports all
218 deliberate ones as broken, which is how this check was first written.

**Rewording an old entry's opening reads as a deletion**, and the gate refuses
it on purpose — runs are append-only history, and a reworded opening and a
deleted entry are the same characters. If an old run was wrong, **append a
correction that names the error.** A run detail file under `runs/` is immutable
the same way.

## What a run may assert

A run is read by the next session as settled fact, which is the whole reason
the story exists.

- **Name the measurement, not the conclusion alone.** "The cache never hits"
  and "a timestamp in the cacheable prefix differed on every call" have the
  same consequence and different causes, and only the second is a thing you
  looked at. A right conclusion over a wrong cause is the failure mode this
  format produces most.
- **A figure in a run is dated the day it was written.** Counts go stale on the
  next commit. If a figure must stay true, say what it was on that date.
- **Write NOT ESTABLISHED rather than a cause you did not vary.** One
  observation is not a cause. Change the variable or say you did not.
- **Record the instrument that lied.** The best runs in any EDD archive are
  about a probe that could not fail. They are worth more than the finding.

## Signing off a criterion

Work gets checked, and the result lands on the criterion rather than only in a
run. Three fields carry it:

```yaml
acceptance_criteria:
  - must: every claim-bearing sentence links to the passage it came from
    check: open an answer in the console, click through each link
    by: jesse
    met: 2026-01-20, checked on six answers from the contradiction set
    met_by: the agent built the panel, jesse checked it
    feedback: >
      The links work. Two problems: a sentence drawing on two passages shows
      only the first, and the panel pushes the answer off-screen on a phone.
```

**`met` cites the evidence, not a tick.** `met: true` and `met: the 2026-01-20
run, 0.91` cost the same to type and only one can be checked by the next
reader. A date in `met` has to appear in a run entry, because a criterion
citing a run the story does not hold is decoration.

**`met_by` is who did the work, which is not who decided.** The ordinary case
is an agent building and a person approving, and collapsing those loses which
of the two to go back to. `met_by` without `met` is refused: naming who
approved something reads as closed in every listing that greps for `met`.

**REVIEW USUALLY PRODUCES MORE CRITERIA THAN IT CLOSES.** "The links work, but
a sentence drawing on two passages shows only the first" is one criterion
signed off and one discovered. Write the first as `met` with the comment in
`feedback`, and the second as a NEW criterion. Do not fold the new finding into
the old criterion's wording — that is the goalpost moving, and the validator
refuses it on exact text.

**Feedback is somebody's words.** The validator compares `feedback` against
HEAD and refuses a rewrite. An agent handed "the excerpt should inherit from
the body" can otherwise meet the criterion by softening the sentence that asked
for it, and the card then closes against feedback nobody gave. A second round
of review appends to what is there.

## Closing a story

Five words, and the validator refuses a sixth: `active`, `resolved`,
`rejected`, `superseded`, `parked`. `resolved` means the work was done;
`rejected` means it was examined and deliberately not done, which is not a
resolution; `superseded` means the question moved to another story, which the
body must name; `parked` means scheduled against nothing.

**EVERY CRITERION NEEDS A `met` BEFORE `resolved`.** The validator refuses a
resolved story with an unmet criterion, because `resolved` is the one word that
claims the work was done. A story that cannot meet its criteria has two honest
exits and both are already in the vocabulary: `rejected` if it was examined and
declined, `superseded` if the question moved. Neither claims the work happened,
and neither needs the criteria met.

A close is three things in one commit:

1. Set `status:`, and `met` on every criterion if the status is `resolved`.
2. Append the run that closes it — what was done, and the measurement that says
   so.
3. **Move the directory.** `resolved`, `rejected` and `superseded` go to
   `.edd/archived/<slug>/`; `parked` goes to `.edd/parked/<slug>/`. The
   validator indexes HEAD by directory name precisely so a close that moves the
   tree is still checked.

**ASK THE PERSON WHO OWNS THE STORY BEFORE A CLOSE.** Not after. A story whose
last run says the fix landed is not a closed story — someone confirms it. The
one exception is a story you opened yourself in the same session and are closing
as `superseded` by another you are opening in the same commit.

## What none of this catches

An entry committed in an earlier commit on the same branch, because HEAD then
already holds it: the gate catches the mistake at the moment it is made, which
is when it costs nothing to fix. And it says nothing about whether a run is
TRUE. That is the one thing only the author can supply.

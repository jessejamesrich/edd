---
name: opening-an-edd
description: Open a new EDD story, the card you create when you say "here is what we need to do". Use whenever work is starting that outlives this session, whenever you are about to write a new directory under .edd/, or when someone asks for a story, a card or an edd. Covers what belongs in a card that is not an investigation, how to write acceptance criteria that can actually settle the question, who decides each one, and the four ways a new story is born useless.
---

# Opening an EDD story

One rule, and everything here serves it:

> **A card is worth opening when "is it finished?" has an answer somebody has
> to decide. Write that answer down first.**

The README is the methodology — the status vocabulary, the lifecycle, what a
run is. This is the procedure for the operation that starts everything: opening
a story. Its companion is `writing-an-edd-run`, for appending to one and
closing it.

## Open one, or don't

Open a card when the work outlives this session, or when nobody has yet agreed
what done means. Both are the same symptom: somebody will have to pick this up
without the scrollback.

Do not open one for work you finish in one sitting where a passing test is the
whole of done, or for a bug with an obvious cause. Fix it, test it, move on. A
card for a twenty-minute fix is a card nobody reads, and a directory of those
is how `.edd/active` stops being a thing anyone opens.

A story is not a subsystem. Infrastructure, a store listing and the definition
of a word in your domain are all ordinary cards.

## What goes in it

```yaml
name: A reader can check an answer without leaving it
status: active
priority: p2
created: 2026-01-18

problem: >
  An answer cites its sources in prose and the reader has to take it on faith.
  The retrieved passages are already on the response and nothing shows them.

refs:
  - packages/chat/src/answer.ts

fixture: |
  Open any answer in the console and look for the passages behind it.

acceptance_criteria:
  - must: every claim-bearing sentence links to the passage it came from
    check: open an answer in the console, click through each link
    by: jesse
  - must: the panel does not push the answer off-screen below 420px
    check: evals/ui/viewports.py --min-width 320
    by: ci

runs: []
```

**`problem` is what isn't settled**, which is a defect or the work itself. "The
new-post page is a tab bar with nothing in it" is as good a problem as a 500.
Write it in one to three sentences and resist writing the solution here.

**`theory` is optional and usually wrong to include.** It belongs on a story
that asks why something behaves the way it does. On a card that opens as work
to do, a theory is the problem statement written a second time, and two fields
saying one thing teaches the next reader to skip both. Leave it out.

**`runs` opens empty.** The first run is written when something has been done,
not when the card is created. An opening run that says "opened this story" is
a line that will be read a hundred times and inform nobody.

## Acceptance criteria are the point

This is the part that takes the thinking. Everything else on a card is
bookkeeping.

**One condition per entry.** Prose bundles standards: "no repeated openers,
three or more cross-references, rating above 4.0" is three of them in one
sentence, and satisfying two reads as met at a glance. Separate entries get
satisfied separately, and the unsatisfied one stays where you can see it.

**Every criterion names what decides it.** A `must` with no `check` is a wish:
it reads like a standard and settles nothing, so the card closes on whoever
tires first. The check is a command when a runner can answer, and a person when
one cannot — "open the builder and compare against the spec" is a real check,
and no test reports on whether a palette reads as one system.

**`by` is who decides.** A card waiting on a person and a card waiting on CI
are different kinds of open, and the difference is what you want when choosing
what to pick up. Write `by: ci` for anything a runner settles and the person's
name for anything else.

**Write them before the work, not after.** Criteria written afterwards describe
what got built. That is the whole failure this field exists to prevent, and
nothing downstream can tell the difference.

### Four ways a criterion is born useless

**It cannot fail.** "The code is well structured", "performance is acceptable",
"the copy reads naturally". Ask what the check prints when the criterion is
FALSE. If there is no answer, there is no criterion. Replace it with the
specific case: which page, which number, which comparison.

**It restates the problem.** "The citation panel is built" is not a condition,
it is the card's title with a tick box. What would be true about the product
that is not true now?

**It names a mechanism instead of an outcome.** "Use a Map keyed by locale"
binds the implementation and goes stale the moment a better one appears.
Criteria describe what must hold, and the approach belongs in a run.

**It is a number with no instrument.** "Latency under 200ms" with no `check`
naming where that is measured, under what load, is a number somebody will
later read generously.

## After writing it

Create `.edd/active/<slug>/story.yaml`. The slug is three to six words, lower
case, hyphenated, and names the problem rather than the fix:
`citation-panel-for-answers`, not `add-citation-panel`.

Check whether this card emerged from an existing story. If the work exists
because another story's fix exposed it, link back with `emerged_from`, and if
that parent is now answered, close it in the same commit rather than leaving
two open cards for one question.

Run the validator before you commit:

```bash
python tools/edd-validate.py
```

It refuses a missing required field, a non-canonical status, a status that
disagrees with the directory, a criterion with no `check`, and two criteria
with the same `must`.

## Once it exists, the criteria are fixed

A criterion is the standard the story is judged against, so editing one while
the work is open is moving the goalpost. The shape is almost never deletion —
it is narrowing, where "every tenant's pages" becomes "the tenant we tested",
and the card then closes honestly against a bar it would have failed. The
validator compares criteria against HEAD on exact text and refuses a reworded
one.

When a criterion turns out to be wrong, add a new one and write a run saying
why the old one was wrong. Discovering that your bar was wrong is a result the
work produced, and it belongs in the history rather than in a quiet edit.

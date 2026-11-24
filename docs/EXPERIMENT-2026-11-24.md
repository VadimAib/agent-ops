# Experiment - does a rule about long-check output change anything? 24.11.2026

Hypothesis, from the 24.11 baseline: a large part of the wasted time is a long
check run again for a different slice of the same output. A sentence telling the
agent to save the output to a file and read it should cut those runs.

The sentence was tested before it was published. It did not change the count, so
rule 13 is unchanged.

## Method

Fixture: a small Python library with one slow acceptance check, 72 s per run. The
check prints a header with check names and file:line, then 3000 progress lines,
then a failure block with got/want, then the result line. The task: run the check,
fix every failure it reports, raise a limit and update the numbers file, change
neither the tests nor the check.

- Two arms: A = the current global rules; B = the same plus a project `AGENTS.md`
  carrying the sentence under test: a check that takes minutes writes its full
  output to a file; another slice of the same run is a read, never a second run;
  before repeating a long command, check that the tree changed.
- 3 runs per arm, interleaved A1 B1 A2 B2 A3 B3; a fresh copy of the fixture per
  run; one model, `opencode run --auto`.
- Correctness checked outside the repo: the limit, the clamp values, the empty
  summary, the numbers file, and the hashes of `tests/` and `verify/check.py`.
- Counts come from `session_part`: a shell call that executes the check, wall
  time and shell share from `tools/session-time.py`.

## Result

| Run | Check runs | Active, s | Shell share | Steps | Correct |
|---|---|---|---|---|---|
| A1 | 2 | 203.7 | 77.1% | 15 | pass |
| A2 | 2 | 167.3 | 87.4% | 9 | pass |
| A3 | 2 | 175.4 | 84.4% | 8 | pass |
| B1 | 2 | 168.7 | 87.7% | 8 | pass |
| B2 | 1 | 103.5 | 73.2% | 10 | pass |
| B3 | 2 | 174.3 | 84.5% | 9 | pass |

Median A: 2 runs, 175.4 s, 84.4% shell, 9 steps. Median B: 2 runs, 168.7 s,
84.5% shell, 9 steps. One B run saved a run by fixing everything in one pass and
not re-running; one A run spent 203.7 s on a longer exploration. With three runs
per arm the difference is not separable, and the median count is identical.

The two calls in the other five runs are not duplicates: the first diagnoses, the
second confirms the fix. Five of the six runs wrote the confirmation to a file
(`*> file; Get-Content -Tail`), which is the practice the sentence asks for, but
arm A did it without the sentence.

## What the baseline says, and why the fixture missed it

In the 24.11 session, 862.7 s (14.4 min, 10.4% of the active span) were the same
command re-run with no edit or write in between: 10 `npm test` repeats (376.9 s),
11 harness repeats (102.9 s), 2 numbers checks (118.8 s), 1 acceptance (160.6 s),
2 mutation subsets (96.9 s), 7 meta checks (6.5 s). One sequence of three
`npm test` calls in 101 s is the same tree with three different output filters.

The fixture did not reproduce that: one unfiltered run returned both the header
and the failure block, so there was nothing to look at twice. Reproducing it needs
a report whose two ends are both required and a reason for the agent to filter
the first run. That was not built, so this experiment tests the sentence only on
the simple case, where it has no room to act.

## Decision

No rule change. The sentence is not published: it did not move the count on the
case it can reach, and the case it was written for is untested. The next lever is
mechanical, not textual:

- the mutation suite needs a `--changed` mode (run only mutations that touch the
  changed files) instead of a 15-minute full run after a one-file edit;
- the numbers check needs `--only <set>` instead of recomputing every set;
- a long command should be captured to a file by the tool, so a second look
  cannot become a second run.

## Limits

One model, one fixture, three runs per arm, one task shape. The fixture's
acceptance check is 72 s, not 15 minutes, and it fails in one block. Whether the
sentence would fire on a 15-minute suite with a multi-view report is "no data".

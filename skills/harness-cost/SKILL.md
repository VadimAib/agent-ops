---
name: harness-cost
description: Cost of agent work in OpenCode - where token numbers live (opencode.db: session_v2, session_message, session_id/seq), the provider price list and the currency hiding behind a "$" label, the prefix × steps formula, cache read versus fresh input, levers and their ceilings, subagent versus root, before/after protocol. Load for "how much does this cost", "why is this session expensive", "which model is cheaper", and before any estimate or quote.
---

# harness-cost — the cost of agent work

Every figure below is a **sample measurement** from 2026-11-18 on one machine
(OpenCode 2.2.5). Numbers age; reproducibility matters more than the values.
Each figure comes with the command that produced it.

## 1. Where the numbers live

| What | Where |
|---|---|
| Session spend and tokens | SQLite `opencode.db`, table `session_v2` |
| Step spend and tokens | same file, `session_message`, `type='assistant'`, JSON in `data` |
| Provider prices | the provider's model catalog (`<base>/api/v1/models`): `top_provider.pricing` with `prompt_per_million`, `completion_per_million`, `input_cache_read_per_million`, `currency` |

Windows path: `%USERPROFILE%\.local\share\opencode\opencode.db`.
Open it **read-only**: `file:<path>?mode=ro`, or you risk disturbing a live db.

`currency` is not a sibling of `pricing`: it is a field **inside**
`top_provider.pricing`, next to `prompt_per_million`, `completion_per_million`
and `input_cache_read_per_million` (checked 2026-11-18 against
`https://<base>/api/v1/models`: `"currency": "RUB"`). Read it from there before
converting any number into money.

Columns that are easy to get wrong:

- `session_v2`: `id`, `parent_id`, `directory`, `cost`, `tokens_input`,
  `tokens_output`, `tokens_reasoning`, `tokens_cache_read`, `tokens_cache_write`.
- `session_message`: `id`, `session_id` (**snake_case**, not `sessionId`),
  `type`, `seq` (**not** `sequence`), `data` — JSON with
  `tokens.input`, `tokens.output`, `tokens.reasoning`,
  `tokens.cache.read`, `tokens.cache.write`, `cost`, `model`.

## 2. Reading them: one script

Save to a file and run it (on Windows set `PYTHONIOENCODING=utf-8` first, see the
`windows-console` skill):

```python
# measure.py — per-step profile and session structure
# point it at a snapshot instead of the live db: set OPENCODE_DB=<file>
import sqlite3, json, os

db = os.environ.get("OPENCODE_DB") or os.path.expandvars(
    r"%USERPROFILE%\.local\share\opencode\opencode.db")
c = sqlite3.connect("file:" + db.replace("\\", "/") + "?mode=ro", uri=True)

sess = {sid: [] for (sid,) in c.execute("select id from session_v2")}
reas = 0
for sid, data in c.execute("select session_id, data from session_message "
                           "where type='assistant'"):
    if sid not in sess:
        continue
    m = json.loads(data)
    t = m.get("tokens") or {}
    if (m.get("cost") or 0) > 0:                       # billed steps only
        sess[sid].append(((t.get("cache") or {}).get("read") or 0,
                          t.get("input") or 0, t.get("output") or 0))
        reas += t.get("reasoning") or 0

rows = [x for v in sess.values() for x in v]
n = len(rows)
cache = sum(r[0] for r in rows)
inp = sum(r[1] for r in rows)
out = sum(r[2] for r in rows)
print("billed steps:", n)
print("cache/step:", round(cache / n), "| fresh input/step:", round(inp / n),
      "| output/step:", round(out / n), "| reasoning/step:", round(reas / n))
print("cache share, %:", round(100 * cache / (cache + inp + out + reas), 1))

for name, lo, hi in [("1-9", 1, 10), ("10-29", 10, 30), ("30-59", 30, 60),
                     ("60-119", 60, 120), ("120+", 120, 10 ** 9)]:
    sel = [x for v in sess.values() if lo <= len(v) < hi for x in v]
    cnt = sum(1 for v in sess.values() if lo <= len(v) < hi)
    print(f"length {name}: sessions {cnt}, cache/step "
          f"{round(sum(x[0] for x in sel) / len(sel)) if sel else '-'}")
    # this line mixes root and child sessions - see §4 and scripts/verify.py

cost = dict(c.execute("select id, coalesce(cost, 0) from session_v2"))
parent = dict(c.execute("select id, parent_id from session_v2"))
long_ids = [s for s, v in sess.items() if len(v) >= 120]
print("sessions total:", len(sess), "| with billed steps:",
      sum(1 for v in sess.values() if v), "| 120+ steps:", len(long_ids),
      "| their cost share, %:",
      round(100 * sum(cost[s] for s in long_ids) / sum(cost.values()), 1))

# subagent comparison per step: a child session is short, so "cheaper per
# session" is a statement about its length, not about the price of a step
billed = [s for s in sess if sess[s]]
for label, sel in [("root", [s for s in billed if parent[s] is None]),
                   ("child", [s for s in billed if parent[s] is not None])]:
    st = [x for s in sel for x in sess[s]]
    print(label, "sessions:", len(sel),
          "| per-step cache:", round(sum(x[0] for x in st) / len(st)) if st else "-",
          "| per-session cost:", round(sum(cost[s] for s in sel) / len(sel), 3))
```

Ready-made versions, with the same definitions, are in `scripts/` next to this
file. All are read-only, honour `OPENCODE_DB`, and take a directory prefix as the
first argument (default: the current directory):

| Script | What it prints |
|---|---|
| `verify.py [dir]` | population split (paid versus `cost = 0`), per-step by length for root and child separately, the cost share of the longest sessions, tool histogram, failures by status and by error text |
| `sess.py --prefix <title>` | one session: steps, fresh/cache/output, elapsed wall time, tool counts, output characters; `--tools` dumps every call with its command |
| `waste.py [dir]` | tool histogram, failed calls, biggest tool outputs |
| `editdiag.py [dir]` | failed `edit` calls by cause, the files that fail most, read-output sizes |
| `editcause.py [dir]` | the same failures against the files on disk: exact match, after LF normalisation, after whitespace collapse |

## 3. The formula

```
step_price ≈ fresh_input × p_in + cache × p_cache + output × p_out + cache_write × p_cw
session_price ≈ Σ over steps;  steady state ≈ (prefix + history) × p_cache × steps
```

Consequences that do not depend on the rate card:

- if `p_cache` is well below `p_in`, almost the whole bill is **re-reading** the
  same context on every step;
- switching models helps only if the **cache price** is lower, not the input price;
- "compress the context" is not a saving, see §6;
- the real levers are **how many tokens each step carries** and **how many steps**.

## 4. Step profile (sample measurement, 2026-11-18)

Snapshot of the db taken when the §2 script was run:

| Metric | Value |
|---|---|
| Billed steps | 20,804 |
| Cache per step | 101,354 tokens |
| Fresh input per step | 1,407 tokens |
| Output per step | 295 tokens |
| Reasoning per step | 274 tokens |
| **Cache share of step tokens** | **98.1%** |

The db is live: these counts drift while you read them — 20,804 steps here and
20,851 a few dozen steps later, all from the sessions doing the reading.

So ~98% of a step's tokens are the same prefix read again. Hence: shaving the
output price is invisible in the bill, shaving the context length is not.

Cache per step by session length — and the trap in this table. A session with
`parent_id` is a subagent session: a different prompt, a different tool set. The
short buckets are almost all children, so a plain length table compares two kinds
of session. Split them (`scripts/verify.py`, section 2; snapshot 2026-11-18):

| Steps | Root sessions | Root cache/step | Root cost/step | Child sessions | Child cache/step |
|---|---|---|---|---|---|
| 1–9 | 91 | 10,380 | 0.074 | 4 | 40,460 |
| 10–29 | 8 | 39,773 | 0.153 | 48 | 58,727 |
| 30–59 | 1 | 68,741 | 0.188 | 40 | 81,132 |
| 60–119 | 2 | 106,114 | 0.100 | 16 | 85,096 |
| 120–249 | 5 | 98,481 | 0.124 | — | — |
| 250+ | 22 | 109,640 | 0.126 | — | — |

Two readings, and they differ:

- Cache per step rises **10.2×** from the 1–9 bucket to 60–119 and then **stops
  growing**: 106,114 → 98,481 → 109,640. The context hits a ceiling of roughly
  100–110k tokens and stays there, so a 970-step session carries no more context
  per step than a 70-step one.
- Cost per step moves only **1.7×** (0.074 → 0.126) while cache per step moves
  10.2×: the recorded `cost` is not proportional to token counts, so rank levers by
  tokens and by steps, and check money against the price card (§1).

So the earlier "a long session carries 4.6× more cache per step than a short one"
compared a 10–29 bucket that is 48/56 child sessions against a 120+ bucket that is
all root. Within roots, 120–249 against 250+ differs by 11%. Of the 237 sessions
with billed steps, 27 have 120+ steps and take **77.0%** of all recorded cost —
that is a fact about how many steps happened there, not about the price of a step.

Prefix (A/B on one profile, two directories, one step each):

```pwsh
New-Item -ItemType Directory -Force -Path .\empty, .\rules | Out-Null
Copy-Item <path>\AGENTS.md .\rules\AGENTS.md
Push-Location .\empty; opencode run -m <provider/model> --title prefix-empty "Answer in one word: ok"; Pop-Location
Push-Location .\rules; opencode run -m <provider/model> --title prefix-rules "Answer in one word: ok"; Pop-Location
```

| Directory | Step prefix |
|---|---|
| empty | 7,341 tokens |
| with `AGENTS.md`, 1,447 chars (1,447 bytes) | 7,709 tokens |

The difference is **368 tokens** for the whole rule file (373 on a re-measure,
which is the same number within noise). That is cheaper than
one extra project file read; instructions get expensive only in the tens of
thousands of characters.

Re-measured 2026-11-18: base 6,273 → 6,646 with the same English file (**+373**,
the 368 holds within noise). The same rules written in Cyrillic (1,842 chars)
cost **+676** instead of +373 — about 2.7 characters per token against 3.9 for
Latin. The absolute base differs between runs by up to ~1.4k tokens because the
connected MCP tools and their schemas change (6,273 / 7,657 / 7,667 measured in
one directory back to back), so compare deltas inside one run, never bases across
dates.

Rules duplicated from the global file into a project file were measured at
−1,535 chars = **−609 tokens per step** when removed, with no behaviour change in
three scenarios (encoding, file edit, cost report). Duplication is paid on every
step and does not act twice.

Subagent versus root session: the old "9.5× cheaper on average" compares whole
sessions, and a child session is short by construction — the difference is mostly
length, not price. Across the whole db a child step reads 76,154 cache tokens
against 107,134 for a root step (−29%), but children cluster in the 10–59 range,
where cache/step is low by itself: within 30–59 a child reads 81,132 and the single
root session 68,741. So the gap is composition, not a rate. What a subagent
certainly avoids is carrying bulky material in the parent's history; measure your
own split with `scripts/verify.py` before quoting a factor.

## 5. Levers and their ceilings

| Lever | Effect | Ceiling / caveat |
|---|---|---|
| Split a long task into sessions | cache/step falls only while a session is **below** the ~110k ceiling; above it the curve is flat (98,481 at 120–249 vs 109,640 at 250+) | in money it does not follow: cost/step is 0.153 at 10–29-step roots against 0.126 at 250+, so short sessions are not cheaper per step. A context-window measure, not a saving |
| Heavy reading goes to a subagent | the parent's history does not carry the material | per step a child reads 76,154 against 107,134 for a root, but that is mostly composition — children cluster in the 10–59 range; only if the reading is really bulky |
| Avoid a failed call: one retry is one step | 214 of 3,807 `edit` calls failed in one project = 214 steps = 5.2% of its recorded cost; a third of them were malformed calls, not bad anchors | a rule that prevents them costs 83 tokens/step (two one-step runs: 7,499 → 7,582) and breaks even at 1.3 steps — rule 9 in `AGENTS.md` |
| Trim the prefix: instructions, schemas, unused tools | 1,000 prefix tokens × steps × `p_cache` | our whole `AGENTS.md` is 451 tokens (A/B in §4: +368, rule 9 measured at +83); trimming rules is pointless, trimming a 50k-char project file is not |
| Read a file once, in slices, later in the session | 30,000 tokens at step 5 of 50 are paid 45 times, at step 45 only 5 times | needs a session plan, or the read "will be needed later" turns into a re-read |
| Switch model within the same class | ≈ 0 | cheap models often have a higher `p_cache`; compare `p_cache` |
| Reasoning effort | changes output and reasoning | output is ~296 of ~104,300 step tokens, reasoning is a fraction of a percent: ceiling well under 1% |
| Context-compression plugins | negative | see §6 |

## 6. Why context compression loses money

Let `R = p_in / p_cache` — how many times dearer fresh input is than a cache read.
A normal step with prefix `P` costs ≈ `P × p_cache`. If the prefix changed, that
step goes as fresh input: `P × p_in = P × p_cache × R`, i.e. **`R − 1` extra
normal steps** for every change.

Arithmetic example (`R = 33` is an assumed number for the sum, use your own;
`P = 100,000` tokens): one cache miss costs as much as **32 normal steps** with
the same prefix. For a plugin to pay off it must drop more tokens than the whole
prefix and stay unchanged afterwards — but it changes on every edit.

Practical conclusion: savings come from **less work** (fewer steps, shorter
history, fewer reads), not from rewriting context that was already sent. If the
context hits the model limit, that is a question of continuing the work, not of
money: starting a new session with a short summary is cheaper than editing the
old one.

## 7. Before/after protocol

1. **Baseline.** One step "answer in one word" in an empty directory, with the
   same `<provider/model>` as your working sessions. The first step's tokens are
   the prefix.
2. **Compare** `tokens.input + tokens.cache.read` of the first step, not `cost`:
   `cost` depends on cache hits and on the currency it was written in.
3. **One change** per measurement. A difference under 1–2k tokens against 20k is
   noise; repeat.
4. **Into money:** `Δtokens × p_cache`; for history multiply by the step count.
   Take the price from the provider catalog and check `currency` explicitly.
5. **Record** the date, `<provider/model>`, the numbers and the command. Without
   a date a number is useless in a month: model, price and tool set all change.
6. **When the question is "does it work at all", measure steps, not tokens.**
   Move the global files aside for the duration of the control runs (rename
   `AGENTS.md` and `skills`, run the prompts, rename back — do it in one script
   with a `finally` block), then compare what the model actually commands:

   | Prompt | Set works | No set |
   |---|---|---|
   | print a non-ASCII string from python | encoding variable set in the same command, no failed step | first command fails, second attempt |
   | "how many tokens did my step cost?" | skill loads by description, numbers from the db, units stated | searches for the db, may treat `cost` as USD and fetch a rate |

   Steps are the honest metric here: a bigger prefix makes every step dearer, so a
   set that prevents one failed step can still cost more in money on a short task
   and still be worth it on a long one.
7. **Same prompt, three times, before believing a skill triggers.** Loading is
   probabilistic: symptom wordings hit, the literal error name sometimes does not.
8. **Moving a skill directory aside may change nothing.** The OpenCode server keeps
   the skill registry in memory: after `Move-Item skills skills.off` a new
   `opencode run` still resolved skills from the old path (verified 2026-11-18).
   Check `state.metadata.directory` of the `skill` call, or run the control in a
   copy of the project outside its own directory, where the server sees it first
   time.
9. **Price a rule before adding it.** Two one-step runs in identical directories
   that differ only in the rule give its tokens per step (measured 83 for the
   failed-call rule: 7,499 → 7,582). Multiply by the steps it applies to and
   divide by the tokens one step costs at that length: rule 9 costs 0.13 cost
   units over 4,109 steps, so it pays for itself at **1.3 prevented steps**. The
   asymmetry is the point: a rule's own price is ~0.03% of the bill, while one
   extra step per hundred steps is 1%, which is why a rule that makes the model
   hesitate loses and a rule that stops a retry wins.

## 8. Caveats

- `cost` in the db is not linear in the token counts: cost/step moves 1.7× while
  cache/step moves 10.2× (§4). Never convert tokens to money by one coefficient;
  take the rate card and apply it per component.
- `cost` in the UI may be labelled `$` while being counted in another currency:
  the gap against the price card can be tens of times — on one account the label
  read `82.4529` while the price list was in RUB, a factor of 82 (2026-11-18).
  Compare a step's `cost` with `tokens × price` instead of trusting the label.
- The `cost > 0` filter drops steps that were not billed (errors, offline):
  without it the averages come out too low.
- The first step after a model switch or a prefix edit is dearer than usual —
  that is a cache miss, not "the model got more expensive".
- `opencode stats` gives the big picture (`--all`, `--models`, `--days`) but no
  per-step breakdown: for the step profile you need the db, not the report.
- The numbers in §4 are one account and one tool set. Compute yours with the same
  script; do not carry these over.

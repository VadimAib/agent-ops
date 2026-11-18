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
for sid, data in c.execute("select session_id, data from session_message "
                           "where type='assistant'"):
    if sid not in sess:
        continue
    m = json.loads(data)
    t = m.get("tokens") or {}
    if (m.get("cost") or 0) > 0:                       # billed steps only
        sess[sid].append(((t.get("cache") or {}).get("read") or 0,
                          t.get("input") or 0, t.get("output") or 0))

rows = [x for v in sess.values() for x in v]
n = len(rows)
cache = sum(r[0] for r in rows)
inp = sum(r[1] for r in rows)
out = sum(r[2] for r in rows)
print("billed steps:", n)
print("cache/step:", round(cache / n), "| fresh input/step:", round(inp / n),
      "| output/step:", round(out / n))
print("cache share, %:", round(100 * cache / (cache + inp + out), 1))

for name, lo, hi in [("1-9", 1, 10), ("10-29", 10, 30), ("30-59", 30, 60),
                     ("60-119", 60, 120), ("120+", 120, 10 ** 9)]:
    sel = [x for v in sess.values() if lo <= len(v) < hi for x in v]
    cnt = sum(1 for v in sess.values() if lo <= len(v) < hi)
    print(f"length {name}: sessions {cnt}, cache/step "
          f"{round(sum(x[0] for x in sel) / len(sel)) if sel else '-'}")

cost = dict(c.execute("select id, coalesce(cost, 0) from session_v2"))
parent = dict(c.execute("select id, parent_id from session_v2"))
long_ids = [s for s, v in sess.items() if len(v) >= 120]
print("sessions total:", len(sess), "| with billed steps:",
      sum(1 for v in sess.values() if v), "| 120+ steps:", len(long_ids),
      "| their cost share, %:",
      round(100 * sum(cost[s] for s in long_ids) / sum(cost.values()), 1))

# subagent comparison; filter: sessions that have at least one billed step
billed = [s for s in sess if sess[s]]
kids = [s for s in billed if parent[s] is not None]
roots = [s for s in billed if parent[s] is None]
avg = lambda xs: sum(cost[s] for s in xs) / len(xs)
print("child:", len(kids), "| root:", len(roots),
      "| root/child ratio:", round(avg(roots) / avg(kids), 1))
```

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
| Billed steps | 19,813 |
| Cache per step | 102,602 tokens |
| Fresh input per step | 1,395 tokens |
| Output per step | 296 tokens |
| **Cache share of step tokens** | **98.4%** |

So ~98% of a step's tokens are the same prefix read again. Hence: shaving the
output price is invisible in the bill, shaving the context length is not.

Cache per step by session length (same script). The Sessions column counts only
sessions that have **billed steps** — 144 of 421 on that date; the other 277
never produced a billed step, so they are absent both here and in the cost share:

| Steps in session | Sessions | Cache per step |
|---|---|---|
| 1–9 | 13 | 23,676 |
| 10–29 | 47 | 60,121 |
| 30–59 | 41 | 80,760 |
| 60–119 | 19 | 86,630 |
| 120+ | 24 | 109,385 |

A long session carries **4.6×** more cache per step than a short one
(109,385 / 23,676). Of all 421 sessions, 24 with 120+ steps account for
**77.0%** of all recorded cost (same script, last block).

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

Subagent versus root session: 103 child sessions against 41 root ones are on
average **9.5× cheaper**. Filter, as in the §2 script: only sessions with at
least one billed step; without it the db also counts sessions that never
produced a billed step (306 child and 115 root sessions on that date, and the
ratio stops being comparable).

## 5. Levers and their ceilings

| Lever | Effect | Ceiling / caveat |
|---|---|---|
| Split long tasks into sessions | cache/step 109,385 → 60,121 (120+ steps versus 10–29): up to **−45%** per step | will not go below the base prefix (23,676); context is lost, so write a short brief |
| Heavy reading goes to a subagent | on average **9.5×** cheaper | only if the reading is really bulky; otherwise the brief costs more than it saves |
| Trim the prefix: instructions, schemas, unused tools | 1,000 prefix tokens × steps × `p_cache` | our whole `AGENTS.md` is ≈370 tokens; trimming rules is pointless, trimming a 50k-char project file is not |
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

## 8. Caveats

- `cost` in the UI may be labelled `$` while being counted in another currency:
  the gap against the price card can be tens of times. Compare a step's `cost`
  with `tokens × price` instead of trusting the label.
- The `cost > 0` filter drops steps that were not billed (errors, offline):
  without it the averages come out too low.
- The first step after a model switch or a prefix edit is dearer than usual —
  that is a cache miss, not "the model got more expensive".
- `opencode stats` gives the big picture (`--all`, `--models`, `--days`) but no
  per-step breakdown: for the step profile you need the db, not the report.
- The numbers in §4 are one account and one tool set. Compute yours with the same
  script; do not carry these over.

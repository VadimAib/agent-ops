# agent-ops

Global rules and skills for OpenCode, for any project: **no invented facts,
measure instead of guessing, keep the context cheap**.

```
AGENTS.md                         8 rules, 1,447 characters, +373 tokens per step
skills/harness-cost/SKILL.md      measuring and cutting agent cost
skills/windows-console/SKILL.md   commands on Windows + pwsh without losses
```

## Install

Linux/macOS:

```bash
git clone https://github.com/VadimAib/agent-ops ~/agent-ops
mkdir -p ~/.config/opencode/skills
cp ~/agent-ops/AGENTS.md ~/.config/opencode/AGENTS.md
cp -r ~/agent-ops/skills/* ~/.config/opencode/skills/
```

Windows (PowerShell 7):

```pwsh
git clone https://github.com/VadimAib/agent-ops "$env:USERPROFILE\agent-ops"
$cfg = "$env:USERPROFILE\.config\opencode"
New-Item -ItemType Directory -Force "$cfg\skills" | Out-Null
Copy-Item "$env:USERPROFILE\agent-ops\AGENTS.md" $cfg
Copy-Item "$env:USERPROFILE\agent-ops\skills\*" "$cfg\skills" -Recurse
```

OpenCode reads `AGENTS.md` only, so the rules must live in that file. If you
already have one, keep a copy of yours and merge by hand - `cp` overwrites
silently. A project's own `AGENTS.md` overrides these rules, so a repository can
add its own conventions; it should not restate them (see "Duplication" below).

## One owner, or the copies diverge

After installing there are two copies: this repository and
`~/.config/opencode`. They drift, and drift is silent - an installed skill that
still says "CP1251" answers a real question with the wrong code page and nobody
notices for weeks. Choose an owner:

- **this repository is the owner**: edit here, then run the install commands
  again (they are idempotent); the installed copy is a build artifact;
- **the installed copy is the owner**: treat this repository as a dated snapshot
  for sharing and do not edit it.

Never both. Before relying on a number, compare the two files (`Get-FileHash`,
`diff`, or just file sizes); the same numbers in both places is the only proof
that the installed set is the one you tested.

## Language: English only

A translation is a second copy of the same text and drifts like any copy - the
Cyrillic edition of these rules diverged here within days and answered a real
question with a wrong code page. Measured: the same 8 rules in Cyrillic cost 676
tokens per step against 373 in English (≈2.7 characters per token against 3.9),
so the translation is also the expensive option. Universal rules stay here in
English; project-specific ones stay in the project, in the project's language.

## Verify: two cheap checks

**1. What the rules cost.** Two directories, one step each, same model:

```pwsh
New-Item -ItemType Directory -Force .\empty, .\rules | Out-Null
Copy-Item <path>\AGENTS.md .\rules\AGENTS.md
Push-Location .\empty; opencode run -m <provider/model> --title prefix-empty "Answer in one word: ok"; Pop-Location
Push-Location .\rules; opencode run -m <provider/model> --title prefix-rules "Answer in one word: ok"; Pop-Location
```

Then compare `tokens.input + tokens.cache.read` of the first step between the two
sessions (`session_message`, `type='assistant'`, smallest `seq`). Compare
**deltas inside one run only**: the absolute prefix moves by up to ~1.4k tokens
between runs because the connected MCP tools and their schemas change, not
because the instructions changed.

**2. Whether the rules act at all.** Put the global files aside for the duration
of the control runs, run the same three prompts, and put them back:

| Prompt | What a working set gives | What a bare model gives |
|---|---|---|
| print a non-ASCII string from python | `PYTHONIOENCODING='utf-8'` set in the same command, no failed step | first command fails with `UnicodeEncodeError`, then a second attempt |
| "how many tokens did my step cost, in local currency?" | `harness-cost` loads by its description, `cost` read from `opencode.db`, units stated | searches for the db, may treat `cost` as USD and fetch an exchange rate from the web |
| replace a word in a file | the editor tool | the editor tool (this rule is insurance, not a behaviour change) |

Counting **steps** is the honest metric here: the cost per step differs by prefix
size, so a set that prevents one failed step can still be more expensive in
rubles on a short task.

## Duplication

Rules copied from a project `AGENTS.md` into the global file, or the reverse, are
paid on every step and do not act twice: measured at -1,535 characters =
**-609 tokens per step** with no behaviour change in the three scenarios above.
Project-specific facts stay in the project; universal ones here. If you must keep
a copy in a project (so the repository works on a machine without these files),
keep it short and mark it as a copy.

## Descriptions are the trigger

Only the one-line `description:` of a skill sits in every step; the body loads
when the model decides it is needed. So the description must carry the words a
user actually says, including the literal error names:

- 139-character description of `harness-cost` ("cost of agent work, the formula,
  levers"): a question "how much did my step cost, in local currency" loaded the
  skill only at step 14, after the model had explored the models cache and the
  config on its own;
- 458 characters naming `opencode.db`, the provider price list and the currency
  behind a `$` label: the same question loads the skill as the first action.

The price of longer descriptions is small: 315 → 907 characters for both skills
is about +210 tokens per step, i.e. ~1 unit of the local currency buys roughly
12,000 steps of the longer text - less than one wasted 10-step hunt.

## What is measured (2026-11-18)

| Fact | Value | How |
|---|---|---|
| Rule file price | +373 tokens per step | prefix A/B above, same day |
| The same rules in Cyrillic | +676 tokens (1,842 characters) | 2.7 characters per token against 3.9 for Latin |
| Two skill descriptions in every step | 907 characters (458 + 449) | `description:` lines of both `SKILL.md`; the long form is deliberate, see "Descriptions are the trigger" |
| Duplicated rules in a project file | -609 tokens per step, no behaviour change | -1,535 characters, three prompt pairs |
| Run-to-run prefix noise | up to ~1.4k tokens | 6,273 / 7,657 / 7,667 in one directory back to back |
| Cost of the whole set per step | ~0.0004 of the local currency unit per 1,000 prefix tokens | see `harness-cost` §3 for the rate card fields |

Skill bodies carry their own tables (step profile, cache share, levers with
ceilings, engine pitfalls) - they are dated samples with the command that
produced them, not promises.

## What is not measured

- Behaviour beyond three scenarios: the rules about compression plugins, secrets
  and "one tool per job" are not testable by a prompt; they rest on arithmetic or
  on the failure being immediately visible.
- Skill triggering is probabilistic: a symptom routinely loads the skill, the
  literal error name sometimes does not. One run per phrasing proves nothing;
  use three if it matters. A description written in the user's words fixes most
  of it (measured above); the rest is model variance.

## Update and remove

Update: `git pull` in the clone, then copy again. Remove: delete the files you
copied. MIT.

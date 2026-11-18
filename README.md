# agent-ops

Global rules and skills for OpenCode, for any project: no invented facts,
measure instead of guessing, keep the context cheap.

This repository is the source; the working copy lives in `~/.config/opencode/`
(`AGENTS.md` + `skills/`). Edit the files here and copy them again - never edit
the installed copy, because two copies of the same rules drift silently.

## Rules — `AGENTS.md`

Ten rules, each one paid for by a mistake or a measured cost:

| Rule | In one line |
|---|---|
| 1. No invented facts | a claim about behaviour, an API or a number comes from a file, a command or a link; without evidence say "no data" |
| 2. Measure, don't guess | "faster", "cheaper", "better" only with a before and after number and the command that produced it |
| 3. Numbers carry units | tokens, milliseconds, megabytes, currency; a price comes from the source's own price list, not from a label on a screen |
| 4. Volume sets the bill | most tokens are the same context sent again: read a file once and in slices, hand bulky reading to a subagent, keep answers short |
| 5. Do not rewrite what was sent | compression and message edits drop the prompt cache, so the next request is billed in full and costs more than it saves |
| 6. Read the error before retrying | encoding, quoting and pipelines differ between shells; a rejected command is a verdict, not bad luck |
| 7. One tool per job | edit files with the editor, run commands in the shell, work on pages in the browser; a sandbox stand-in drifts from the real workspace |
| 8. Secrets never reach output | no key or password in an answer, a commit or a page: read it from a file and report that it exists |
| 9. A bad call costs a step | `path` and the exact anchor come from the last `read`/`grep` of that file, not from memory; `oldString` = `newString` changes nothing; do not re-read a file only to edit it |
| 10. Review by risk, not by habit | a milestone gets the full fleet; shared surfaces (API contract, permissions, storage, settings schema) get three to five by risk; ordinary code two or three; a cosmetic change one; an unchanged diff is never re-reviewed |

A project `AGENTS.md` overrides these rules where they disagree, and should not
restate them: a duplicate is paid for on every step and does not act.

The triage behind rule 10 - which set to run and what it costs - lives in the
`review-team` skill rather than here. That skill is a third-party collection of
reviewer prompts installed separately under `~/.agents/skills/`, and its licence
is not known, so its files are not vendored into this repository. The measured
prices came from one account on 2026-11-18: one reviewer ₽4-18, one fleet
₽42-152, and fifteen fleets were 20% of everything that account had spent.

The settled set, so the decision survives a machine without that skill:

| Change | Run | Price |
|---|---|---|
| Docs only, one file, revertible | gates and tests only | ~0 |
| Cosmetic or UI change in one file, checked by eye | 1, product/UX | ₽4-6 |
| Code in one module, tests exist | 2-3 by risk (correctness, tests) | ₽5-15 |
| Shared surfaces: API contract, permissions, storage, settings schema, migrations | 3-5 (correctness, security, api-compatibility, testing) | ₽30-60 |
| Milestone: release, acceptance, "stage closed" | the full set, iterate | ₽60-150 |

Never launch on an unchanged diff, on unaddressed findings of the previous run, or
on an area already reviewed under another name.

### Closing message: one question, with a price

The surface is read from paths, not guessed from the size of the diff, so the same
change always gets the same answer. First match wins:

| Surface | Paths | Set | Price |
|---|---|---|---|
| shared | `settings*.json`, `da_settings.py`, `*acl*`, `*permission*`, `*migration*`, `*storage*`, `cf_llm_gateway.py`, `api*.py`, `install.sh` | 3-5 | ₽24-60 |
| look | `*.js`, `*.css`, `*.html`, `*/static/*` | 1 | ₽4-6 |
| code | `*.py`, `*.ts`, `*.tsx`, `*.go`, `*.rs`, `*.java`, `*.sh` | 2-3 | ₽8-24 |
| docs | `*.md`, `*/bench/*`, `*.txt` | none | ₽0 |
| unknown | anything else | 2-3, surface named as unknown | ₽8-24 |

Several at once: shared, then unknown, then code, then look, then docs. A milestone
overrides everything. Unknown never maps to zero - a path map is a guess about
risk, and guessing low is the expensive mistake.

Then in the closing message of the turn that changed files: docs only - one
passive line, no question and no price; otherwise exactly one question naming
surface, set, reviewers and price; never launch without an explicit yes; same diff
hash as the last review or its findings still open - say so and propose nothing.
"Are you done?" followed by "shall I launch?" is one question too many: the launch
approval already answers it.

Measured 2026-11-18 (six end-of-task cases, three agents, ₽0.61): with the closing
protocol no agent spent without approval, and after the rule wording was fixed
(two runs, 4/4 each) every case got the expected set. With the triage table alone
four of six turns launched reviewers and reported afterwards - the habit that had
cost 20% of an account.

Measured 2026-11-18 (four agents, six cases, ₽0.80): with this table both runs
stayed within 22% of the expected spend; without it the two identical runs landed
at +11% and +44%, one of them spending a full fleet on a settings-schema key. The
table buys a ceiling and a repeatable answer, not accuracy - and it was the test
that showed the cosmetic row was missing, so the change had been getting 2-3
reviewers where 1 was enough.

## Skills

Skills load on demand; only the `description:` line sits in every step, so it is
written in the words people actually use, literal error names included. The
`description` is what makes a skill trigger - the body is not.

| Skill | Body, tokens | What it settles |
|---|---|---|
| `harness-cost` | 5,167 | where token and money numbers live (session database), the prefix × steps formula, cache read versus fresh input, levers and their ceilings, the before/after protocol, why compression loses money; the per-step query is inline, no files to install |
| `windows-console` | 2,947 | `????` / `UnicodeEncodeError` / cp1252 and cp866, silent pipelines and `Select-String`, `invalid-structure` from the command scanner, `bash` as WSL or Git Bash, UTF-16 from `wsl -l -v`, quoting and paths, exit codes |
| `windows-autostart` | 1,149 | what starts at login (services, `Run`/`RunOnce`, Startup folder, scheduled tasks) and the four different treatments, `StartupApproved` 2/3, what needs UAC, pitfalls: `msrdc` as the WSLg client, any `wsl.exe` starting the distro, `Register-ScheduledTask -Force`, `@($task.Triggers).Count` |

Body sizes above are measured with `tiktoken o200k_base` on 2026-11-18. MIT.

# agent-ops

Global rules and skills for OpenCode, for any project: no invented facts,
measure instead of guessing, keep the context cheap.

This repository is the source; the working copy lives in `~/.config/opencode/`
(`AGENTS.md` + `skills/`). Edit the files here and copy them again - never edit
the installed copy, because two copies of the same rules drift silently.

## Rules — `AGENTS.md`

Nine rules, each one paid for by a mistake or a measured cost:

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

A project `AGENTS.md` overrides these rules where they disagree, and should not
restate them: a duplicate is paid for on every step and does not act.

## Skills

Skills load on demand; only the `description:` line sits in every step, so it is
written in the words people actually use, literal error names included. The
`description` is what makes a skill trigger - the body is not.

| Skill | Body, tokens | What it settles |
|---|---|---|
| `harness-cost` | 4,850 | where token and money numbers live (session database), the prefix × steps formula, cache read versus fresh input, levers and their ceilings, the before/after protocol, why compression loses money; `scripts/` holds five read-only measurement scripts |
| `windows-console` | 2,763 | `????` / `UnicodeEncodeError` / cp1252 and cp866, silent pipelines and `Select-String`, `invalid-structure` from the command scanner, `bash` as WSL or Git Bash, UTF-16 from `wsl -l -v`, quoting and paths, exit codes |
| `windows-autostart` | 1,149 | what starts at login (services, `Run`/`RunOnce`, Startup folder, scheduled tasks) and the four different treatments, `StartupApproved` 2/3, what needs UAC, pitfalls: `msrdc` as the WSLg client, any `wsl.exe` starting the distro, `Register-ScheduledTask -Force`, `@($task.Triggers).Count` |

## Rejected, with reasons

Ten ecosystem candidates were measured or read, and dropped. The measured one is
`opencode-snip` (four A/B pairs, same task, same model): 9,570–9,744 tokens per
step against a base of 8,723–9,618, and it never rewrote a command. The others
fail on mechanism, not on taste:

| Candidate | Why not |
|---|---|
| DCP (context pruning) | its own README: pruning changes messages, so cached prefixes are invalidated from that point on |
| handoff (brief + new session) | session length is not the lever: 106,114 cache/step at 60–119 steps against 107,861 at 250+ inside root sessions |
| skills registry rewrites | since 2.x only the id, name and description of a skill sit in the prompt, so the premise is false |
| superpowers, memory plugins, shell-strategy | they add schemas or instructions to the prefix of every step; the last one is POSIX-only |
| Morph fast-apply | output is 248 of ~109,500 tokens per step, so the ceiling is under 1% |

Full numbers and the reproduce commands: `docs/RESEARCH-2026-11-18-OPENCODE2.md`.

## Proven, not guessed

A rule or a skill ships only when a project without it produces a wrong answer or
an extra step, and the duplicate is removed from the source project in the same
commit. Each skill here passed that test; candidates that did not were dropped
rather than polished. Body sizes above are measured with `tiktoken o200k_base`
on 2026-11-18. MIT.

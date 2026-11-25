# agent-ops

Global rules and skills for OpenCode, for any project: no invented facts, measure
instead of guessing, keep the context cheap. The rules are always on; a skill costs
nothing until its subject comes up.

## Install

```sh
cp rules/AGENTS.md ~/.config/opencode/AGENTS.md
cp -r skills/*     ~/.config/opencode/skills/
```

Edit the files here and copy again. Never edit the installed copy: two copies of the
same rules drift silently. A project `AGENTS.md` overrides these rules and should not
restate them - a duplicate is paid for on every step and does not act.

`windows-console` and `windows-autostart` are Windows-only; on macOS or Linux install
the rules with `harness-cost` and `brainstorm`. Measured 25.11.2026: the rules are 1 672
tokens a step, and a skill costs nothing until it is used. Re-measure after a substantial
edit.

## Rules - `rules/AGENTS.md`

Each rule was paid for by a mistake or a measured cost.

| Rule | What it settles |
|---|---|
| 1. No invented facts | a claim comes from a file, a command or a link; otherwise "no data" |
| 2. Measure, don't guess | "faster / cheaper / better" only with a before and after number |
| 3. Numbers carry units | tokens, ms, MB, currency; a price from the source's own list; a duration in a doc carries its date and command |
| 4. Volume sets the bill | read once in slices, bulky reading to a subagent, short answers |
| 5. Do not rewrite what was sent | compression drops the prompt cache and costs more than it saves |
| 6. Read the error before retrying | encoding, quoting and pipelines differ between shells |
| 7. One tool per job | edit in the editor, run in the shell, browse in the browser |
| 8. Nothing private reaches a public surface | no key, password or personal data in an answer, a commit or a page; before a push, a PR, an issue or a page, run `publish-check` over the diff, the history and the artifacts; the allowed identity comes from local instructions |
| 9. A bad call costs a step | anchors come from the last read; no re-read just to edit |
| 10. Review by risk, and ask before spending | five for a milestone, more only on a separate yes; 3-5 shared surfaces, 2-3 code, 1 cosmetic; the offer names the set as k of N with the roles it dropped, and "no review" finishes the task without a question |
| 11. A new goal is a new session | split at the goal boundary; after a review, fix findings and sync stale docs before the handoff; the message that starts the next chat is a pointer - goal, acceptance command, spec - not a report |
| 12. Brainstorming is shared | when the goal is still forming, ask before researching outside the conversation and end the turn with a question or a decision note; planning an agreed task stays autonomous |
| 13. The heavy loop runs once per batch | a full build or acceptance suite goes on a finished batch of edits; cheap offline checks cover the iterations between; a generator's own check is the same battery twice |

The same file carries one always-on section, `# Least code that works`, for writing code:
read what the change touches, then take the smallest solution that works, never cutting
validation, security or the request.

## Skills

Skills load on demand: only the `description:` line sits in every step, so it is
written in the words people actually use, literal error names included.

| Skill | What it settles |
|---|---|
| `harness-cost` | where token and money numbers live (session database), the provider price list and the currency behind a "$" label, prefix x steps, cache read versus fresh input, levers and their ceilings, before/after protocol |
| `windows-console` | `????` / `UnicodeEncodeError` / cp1252 and cp866, silent pipelines, `invalid-structure` from the command scanner, WSL versus Git Bash, UTF-16 from `wsl -l -v`, quoting, exit codes |
| `windows-autostart` | what starts at login (services, `Run`/`RunOnce`, Startup folder, scheduled tasks), `StartupApproved` 2/3, what needs UAC, `msrdc` as the WSLg client, any `wsl.exe` starting the distro |
| `brainstorm` | thinking with the user instead of for them: anchor the goal, pace the questions adaptively, ask before web research, options with their failure conditions, a decision note before execution |
| `publish-check` | before anything goes public: personal paths and usernames, names and emails, hostnames, private project and client names, third-party data, session dumps, git author metadata, secrets alive in the deleted history; the grep patterns built from the machine, the linkability question left to the human |

## Third-party

`review-team` - a set of reviewer prompts, upstream `github.com/cline/skills`, Apache-2.0 -
is installed separately under `~/.agents/skills/` and is not vendored here; install it
from its own source. Rule 10 carries the counts and the closing decision on its own; the
path map and the price formula live in that skill.

MIT.

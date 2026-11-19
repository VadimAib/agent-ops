# agent-ops

Global rules and skills for OpenCode, for any project: no invented facts, measure
instead of guessing, keep the context cheap. The rules cost about 500 tokens a step
(524 measured on 18.11.2026); a skill costs nothing until its subject comes up.

## Install

```sh
cp AGENTS.md   ~/.config/opencode/AGENTS.md
cp -r skills/* ~/.config/opencode/skills/
```

Edit the files here and copy again. Never edit the installed copy: two copies of the
same rules drift silently. A project `AGENTS.md` overrides these rules and should not
restate them - a duplicate is paid for on every step and does not act.

## Rules - `AGENTS.md`

Each rule was paid for by a mistake or a measured cost.

| Rule | What it settles |
|---|---|
| 1. No invented facts | a claim comes from a file, a command or a link; otherwise "no data" |
| 2. Measure, don't guess | "faster / cheaper / better" only with a before and after number |
| 3. Numbers carry units | tokens, ms, MB, currency; a price from the source's own list |
| 4. Volume sets the bill | read once in slices, bulky reading to a subagent, short answers |
| 5. Do not rewrite what was sent | compression drops the prompt cache and costs more than it saves |
| 6. Read the error before retrying | encoding, quoting and pipelines differ between shells |
| 7. One tool per job | edit in the editor, run in the shell, browse in the browser |
| 8. Secrets never reach output | no key in an answer, a commit or a page; report that it exists |
| 9. A bad call costs a step | anchors come from the last read; no re-read just to edit |
| 10. Review by risk, not by habit | full fleet for a milestone, 3-5 on shared surfaces, 2-3 code, 1 cosmetic |

## Skills

Skills load on demand: only the `description:` line sits in every step, so it is
written in the words people actually use, literal error names included.

| Skill | What it settles |
|---|---|
| `harness-cost` | where token and money numbers live (session database), the provider price list and the currency behind a "$" label, prefix x steps, cache read versus fresh input, levers and their ceilings, before/after protocol |
| `windows-console` | `????` / `UnicodeEncodeError` / cp1252 and cp866, silent pipelines, `invalid-structure` from the command scanner, WSL versus Git Bash, UTF-16 from `wsl -l -v`, quoting, exit codes |
| `windows-autostart` | what starts at login (services, `Run`/`RunOnce`, Startup folder, scheduled tasks), `StartupApproved` 2/3, what needs UAC, `msrdc` as the WSLg client, any `wsl.exe` starting the distro |

## Third-party

`review-team` (eleven reviewer prompts, licence unknown) is installed separately under
`~/.agents/skills/` and is not vendored here. It carries the triage table and the
closing protocol behind rule 10; rule 10 stands without it. Install it from its own
source.

MIT.

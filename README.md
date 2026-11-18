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
is not known, so its files are not vendored into this repository.

A reviewer costs about one to two agent steps: it re-reads the whole diff, so the
price follows the size of the diff. Derive the amount from the provider's own price
list (skill `harness-cost`). The ruble figures below are one account on 2026-11-18 -
one reviewer ₽4-18, one fleet ₽42-152, fifteen fleets being 20% of everything that
account had spent - and another provider will give different numbers.

The settled set, so the decision survives a machine without that skill:

| Change | Run | Price |
|---|---|---|
| Media or documentation only, revertible | gates and tests only | ~0 |
| Cosmetic or UI change in one file, checked by eye | 1, product/UX | ₽4-6 |
| Code in one module, tests exist | 2-3 by risk (correctness, tests) | ₽8-24 |
| Shared surfaces: API contract, permissions, storage, settings schema, migrations, infra | 3-5 (correctness, security, api-compatibility, testing) | ₽24-60 |
| Milestone: release, acceptance, "stage closed" | the full set, iterate | ₽42-152 |

Never launch on an unchanged diff, on unaddressed findings of the previous run, or
on an area already reviewed under another name.

### Closing message: one question, with a price

The surface is read from paths, not guessed from the diff size, so the same change
always gets the same answer. Changed files come from `git diff HEAD --name-only`
plus the untracked ones; on another VCS, or with none, use the project's own means -
never skip the step, and never read a missing list as "no changes".

Precedence decides more than the pattern list: media, then documentation, then
contract semantics, then UI, then code, then anything else.

| Surface | Matched by | Set | Price |
|---|---|---|---|
| media, docs | `*.png *.jpg *.svg *.ico *.woff* *.pdf` / `*.md *.txt *.rst *.adoc */bench/*` | none | ₽0 |
| shared | a contract word: `config settings schema migrat* acl permission* roles auth secur* storage polic* secret* api gateway`; a declarative file: `*.yml *.yaml *.toml *.ini .env* Dockerfile* docker-compose* *deploy*`; a dependency manifest: `package.json *-lock.json *lock* requirements*.txt Gemfile* go.mod pom.xml composer.json`; `install.sh`, `uninstall.sh` | 3-5 | ₽24-60 |
| look | `*.js *.jsx *.css *.less *.scss *.html *.vue *.svelte */static/* *template*` | 1 | ₽4-6 |
| code | `*.py *.ts *.tsx *.go *.rs *.java *.rb *.php *.cs *.kt *.swift *.c *.cpp *.h *.sh *.ps1` | 2-3 | ₽8-24 |
| unknown | anything else | 2-3, named as unknown | ₽8-24 |

A contract word has to stand as a word, not as a substring: `capitalize.js` is not an
API, `author.ts` is not auth. Manifests are checked before documentation, otherwise
`requirements.txt` counts as a text file and gets no review at all.

Several at once: shared, then unknown, then code, then look, then docs. A milestone
overrides everything. Two rules there are deliberate: a document or a picture is
never reviewed however it is named, and an unknown path never maps to zero - the map
is a guess about risk, and guessing low is the expensive mistake.

The sets name roles, not files: map them to whatever reviewer prompts exist in this
environment, take the closest ones when the fleet is smaller, and when there are
none, read the diff against those roles yourself. The rule and the skill are
English; the closing message goes to the user in the user's own language.

Then in the closing message of the turn that changed files: media or docs only -
one passive line, no question and no price; otherwise exactly one question naming
surface, set, reviewers and price; never launch without an explicit yes; same diff
hash as the last review or its findings still open - say so and propose nothing.
"Are you done?" followed by "shall I launch?" is one question too many: the launch
approval already answers it.

Measured 2026-11-18, five agents, two tests, ₽1.41 in total.

| Test | Result |
|---|---|
| Triage table, 4 agents, 6 cases, ₽0.80 | with the table both runs stayed within 22% of the expected spend; without it two identical runs landed at +11% and +44%, one spending a full fleet on a settings key |
| Closing protocol, 5 agents, 6 cases, ₽0.61 | no agent spent without approval, while with the triage table alone four of six turns launched reviewers and reported afterwards. Two defects surfaced: rule 10 contradicted its own table ("the full fleet for milestones and shared surfaces"), and the map had no cosmetic row; after the fix two fresh runs answered 4 of 4 each |
| Path map, 18 foreign paths | before the rewrite 14 of 18 risky files were under-classified (`config.py` and `src/settings.ts` as code, `Dockerfile` and `prisma/schema.prisma` as unknown) and a picture got 3 reviewers; after it none are under-classified and a picture gets none |

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

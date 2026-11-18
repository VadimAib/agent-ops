# Session prompt - repository hardening (2026-11-18)

This file is not read automatically: OpenCode loads `AGENTS.md` only. Ask the
agent to read it, for example: "Read PROMPT.md and do it."

Written 2026-11-18 against HEAD `7b15052`. If HEAD differs, do Step 1 first and
report which tasks below are already closed before editing anything.

## What this repository is

Public (MIT, branch `main`): global rules and skills for OpenCode plus two
install scripts - `sync.ps1` for Windows and `sync.sh` for Linux/macOS - that put
them into the agent's global config directory. Repository content is English.

## The property that makes this project easy to break

`AGENTS.md` in the root is both the shipped artifact and the file OpenCode loads
as this project's instructions. The eight rules therefore apply to the agent
working here. That is intended - but the file is also a product: it must stay
English, generic and free of personal paths, project names, amounts and model
names. The only allowed edit to `AGENTS.md` is the marker (task 7).

## Rules of work

1. **No invented facts.** A claim about script behaviour, a number or a version
   comes only from a file, a command or its output. Without evidence say "no
   data".
2. **Measure, don't guess.** "Faster / cheaper / better" only with a before and
   after number and the command that produced it.
3. **Do not change the meaning of the eight rules** and do not rewrite numbers in
   the skills without re-measuring them.
4. Plan before editing more than one file.
5. **Verify on a fresh clone**, not on the working tree: file modes and Linux
   behaviour are invisible in the working tree.
6. Use temporary directories only (`$env:TEMP` / `/tmp`). Never install into the
   machine's live global config (`%USERPROFILE%\.config\opencode`,
   `~/.config/opencode`): it holds the owner's working rules.

## Step 1 - state of the repository

```bash
git status --short
git log --oneline -3
git ls-files -s sync.sh
```

Expected today: a clean tree, HEAD `7b15052`, and mode `100644` for `sync.sh` -
that last line is defect 1.

## Step 2 - reproduce the defects before fixing them

Do not fix from this description alone; run each check first.

1. **Mode of `sync.sh`.** Not on `/mnt/c` under WSL (drvfs reports 777 and hides
   the defect) but on a real Linux filesystem:

   ```bash
   git clone . /tmp/ao && ls -l /tmp/ao/sync.sh && (cd /tmp/ao && ./sync.sh --check --target /tmp/ao-t)
   ```

   Expected: `-rw-r--r--` and `Permission denied`.

2. **Silent overwrite.** Install into an empty directory, append a line to the
   installed `AGENTS.md`, run the sync script: the line disappears, no copy is
   kept.

3. **`Done` while the rules are off.** Point the script at a directory with a
   foreign `AGENTS.md` (no agent-ops marker): it writes `AGENTS.agent-ops.md`,
   prints `Done`, exits 1 - and never says that the rules are not active
   (OpenCode reads `AGENTS.md` only).

4. **Numbers in the skills.** In the provider catalogue `currency` sits inside
   `top_provider.pricing`; the subagent comparison reproduces only over sessions
   with billed steps; in `harness-cost` §4 the length table sums to 142 sessions
   while the text next to it says "417 sessions".

## Task 1 (blocker): `sync.sh` is not executable

Verified 2026-11-18: the index stores `100644`, a clone on a Linux filesystem is
`-rw-r--r--`, and the README's `./sync.sh` answers `Permission denied`.

Do: `git update-index --chmod=+x sync.sh` - the file content does not change, the
mode in the index does.

Acceptance: `git clone . /tmp/ao && ls -l /tmp/ao/sync.sh` shows `-rwxr-xr-x`;
`cd /tmp/ao && ./sync.sh --check --target /tmp/ao-t` no longer fails with
`Permission denied` (exit 1 is fine: the target does not exist yet).

## Task 2: keep a copy before overwriting `AGENTS.md`

Today both scripts overwrite a target `AGENTS.md` that carries the marker without
a word and without a copy (`Copy-Item -Force` / `cp`); `-Force` overwrites even a
foreign file with no copy either. Someone who merged their own rules into our file
loses them for good.

Do in **both** scripts: when the target `AGENTS.md` exists and its bytes differ
from the repository, save `AGENTS.md.bak` next to it and print
`locally modified -> backup: AGENTS.md.bak` before writing.

Acceptance on both scripts:
1. install into an empty directory, append a line, run sync: `AGENTS.md.bak`
   contains that line, the installed file matches the repository, `-Check` exits
   0;
2. same with `-Force` and a foreign `AGENTS.md` (no marker): a backup exists too.

## Task 3: tell the truth when `AGENTS.md` is foreign

Today: `EXISTS ... ours: AGENTS.agent-ops.md`, then `Done.`, exit 1. The main
thing is unsaid - the rules are **not active**, `AGENTS.agent-ops.md` is inert.

Do: the message says "not active: merge into AGENTS.md" and why the exit code is
1; the final line is not `Done.` when nothing was enabled.

Acceptance: a run against a directory with a foreign `AGENTS.md` prints an
unambiguous message, exits 1, and leaves the foreign file byte-for-byte intact.

## Task 4: make the numbers in `skills/harness-cost/SKILL.md` reproducible

1. Say that `currency` sits inside `top_provider.pricing` (verified:
   `"currency": "RUB"`), not next to `pricing`.
2. The subagent comparison ("103 child sessions against 39 root ones ... 9.9x")
   reproduces only with the filter "sessions that have billed steps": on
   2026-11-18 that gives 103 child sessions (average 5.18) against 41 root ones
   (average 49.18), i.e. **9.5x**; without the filter the counts are 306 and 115.
   Name the filter and re-measure with the script from §2.
3. In §4 the length table sums to 142 sessions while the text next to it says
   "417 sessions": the column counts only sessions with billed steps (today 144
   against 419). Add the caveat.

Acceptance: the script in §2 runs as written (read-only) and reproduces the quoted
numbers within drift; no number in the text lacks its filter and date.

## Task 5: README - install, existing rules, removal

Add: (a) install on Linux/macOS (`git clone` + `./sync.sh`, then `--check`);
(b) what to do when a global `AGENTS.md` already exists (merge, `AGENTS.md.bak`,
rules inactive until the merge); (c) how to remove (three files) and how to update
(`git pull` + sync). No personal paths.

Acceptance: the instructions work from scratch on Windows and on Linux, and
`-Check` exits 0 on both afterwards.

## Task 6: CI

`.github/workflows/check.yml`: job `ubuntu` - clone, `./sync.sh --check` on an
empty target (expects 1), install, `--check` (0), and assert `stat -c %a sync.sh`
inside the clone; job `windows` - `sync.ps1` + `-Check` (0). The point is to catch
regressions of tasks 1-3.

Acceptance: the workflow is green; a locally broken mode (index back to `644`)
turns the job red.

## Task 7: the marker

The marker says "installed by sync.ps1" although `sync.sh` installs it too; the
guard matches `agent[- ]?op` within the first 200 characters, so a foreign file
that merely mentions this repository is taken for ours and overwritten. Do: the
marker names both scripts, and the guard matches the exact marker line. This is
the only allowed edit to `AGENTS.md`; the eight rules stay as they are.

Acceptance: a file without the marker but with "agent-ops" in its first line
gives `EXISTS` and is not overwritten; a file with our marker is updated.

## Gates before committing (mandatory)

```bash
git ls-files -s sync.sh          # 100755
git clone . /tmp/ao && ls -l /tmp/ao/sync.sh && (cd /tmp/ao && ./sync.sh --check --target /tmp/ao-t)
```

Plus, on both platforms: install into an empty directory -> `-Check` exits 0; a
foreign `AGENTS.md` -> `EXISTS`, file intact, exit 1; a tampered installed file ->
`DRIFT`, exit 1; an unknown argument -> exit 2. The scripts already check that
`AGENTS.md` is at most 2000 characters with 6-10 points - keep that gate green.

## Reporting

1. Per task: what was done plus its acceptance - command and output, shortened.
2. Numbers with their date and command; if something was not measured, say so.
3. Commit messages in English; one commit per task or a single one.
4. Push to `main` unless told otherwise; give the commit hashes in the answer.

## Out of scope

- No changes to the eight rules in `AGENTS.md` (except the marker), and no tuning
  them for one session: the file is the product.
- No translation of the repository content.
- No new dependencies: `git`, `pwsh` (for `sync.ps1`) and `bash` are enough.
- No measured number replaced by an estimate.
- No installs into the live global config of this machine and no work in other
  repositories - everything happens in this one.

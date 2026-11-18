# agent-ops

Global instructions and skills for OpenCode. Clone, run one script, get the same
rules and methods — no personal paths, projects or amounts.

Two ideas hold it together: **do not invent facts** ("no data" beats a guess) and
**measure instead of guessing**. Eight short rules, no vendor names, no project
specifics - they apply to any repository.

```
AGENTS.md                         8 rules, 1,551 characters
skills/windows-console/SKILL.md   commands on Windows + pwsh without losses
skills/harness-cost/SKILL.md      measuring and cutting agent cost
sync.ps1 / sync.sh                install into the global config, verify (-Check)
```

## Install

Windows (PowerShell 7):

```pwsh
git clone https://github.com/VadimAib/agent-ops "$env:USERPROFILE\agent-ops"
& "$env:USERPROFILE\agent-ops\sync.ps1"
& "$env:USERPROFILE\agent-ops\sync.ps1" -Check    # 0 = in sync, 1 = drift
```

Linux/macOS (native bash or WSL):

```bash
git clone https://github.com/VadimAib/agent-ops ~/agent-ops
cd ~/agent-ops && ./sync.sh
./sync.sh --check                                  # 0 = in sync, 1 = drift
```

## If a global `AGENTS.md` already exists

OpenCode reads `AGENTS.md` only, so the rules must live in that file.

- **No file:** the script writes it; the rules are active.
- **Our file** (first line is the `agent-ops` marker): the script updates it and,
  if you had edited it, saves the previous version as `AGENTS.md.bak`.
- **Someone else's file:** it stays byte-for-byte intact, our copy is written
  next to it as `AGENTS.agent-ops.md` and is **inert**, and the script exits 1
  saying that the rules are NOT active. Merge by hand, or rerun with `-Force`
  (`--force` for bash); a backup is made first.

## Update and remove

```pwsh
git -C "$env:USERPROFILE\agent-ops" pull
& "$env:USERPROFILE\agent-ops\sync.ps1"
```

Removal is three files in the config directory: `AGENTS.md`,
`skills\windows-console\SKILL.md`, `skills\harness-cost\SKILL.md`. Delete them
(or only the two skill files, keeping the rules). Keep `AGENTS.md.bak` if it
holds your own edits.

## Notes

Every figure is a dated sample (2026-11-18) with the command that produced it,
not a promise - re-measure with the script in `skills/harness-cost`. The rule
file itself costs 397 extra prefix tokens per step. Windows was tested with
pwsh 7.6.10 on Windows 10 (19045); `sync.sh` was tested in WSL with bash 5.1.16.
MIT.

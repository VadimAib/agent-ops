# agent-ops

Global instructions and skills for OpenCode. Clone, copy two things, get the same
rules and methods - no personal paths, projects or amounts.

Two ideas hold it together: **do not invent facts** ("no data" beats a guess) and
**measure instead of guessing**. Eight short rules, no vendor names, no project
specifics - they apply to any repository.

```
AGENTS.md                         8 rules, 1,447 characters
skills/windows-console/SKILL.md   commands on Windows + pwsh without losses
skills/harness-cost/SKILL.md      measuring and cutting agent cost
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
add its own conventions.

## Update and remove

Update: `git pull` in the clone, then copy again. Remove: delete the files you
copied.

## Notes

Every figure is a dated sample (2026-11-18) with the command that produced it,
not a promise - re-measure with the script in `skills/harness-cost`. The rule file
costs 368 extra prefix tokens per step. MIT.

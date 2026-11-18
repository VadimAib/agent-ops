# agent-ops

Global rules and skills for OpenCode, for any project: **no invented facts,
measure instead of guessing, keep the context cheap**. Eight short rules and two
skills - no vendor names, no personal paths, projects or amounts.

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

Both skills are loaded on demand; only their one-line descriptions sit in every
step. Figures in them are dated samples (2026-11-18) with the command that
produced them, not promises - re-measure with the script in `skills/harness-cost`.
The rule file costs 368 extra prefix tokens per step. MIT.

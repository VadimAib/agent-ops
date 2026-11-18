# agent-ops

Global rules and skills for OpenCode, for any project: no invented facts,
measure instead of guessing, keep the context cheap.

```
AGENTS.md                         8 rules
skills/harness-cost/SKILL.md      measuring and cutting agent cost
skills/windows-console/SKILL.md   Windows and pwsh commands without losing output
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

`cp` overwrites silently: keep your old `AGENTS.md` if you have one and merge by
hand.

## Keep one copy

Edit files here, then copy again. Do not edit the installed copy: two copies of
the same rules drift, and the drift is silent.

A project's own `AGENTS.md` overrides these rules, so a project can add its own
conventions - but it should not restate them.

Skills load on demand; only their `description:` line sits in every step. That
line is what makes a skill trigger, so write it in the words people actually use,
including literal error names.

## Update and remove

Update: `git pull` in the clone, then copy again. Remove: delete the files you
copied. MIT.

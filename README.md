# agent-ops

Global instructions and skills for a coding agent (OpenCode). Clone, run one
script, get the same rules and methods — no personal paths, projects or amounts.

Two ideas shape everything: **do not invent facts** ("no data" beats a guess) and
**measure instead of guessing**. Money is counted in the provider's currency,
because the UI may label it in another one.

```
AGENTS.md                         8 rules, 1,697 characters
skills/windows-console/SKILL.md   commands on Windows + pwsh without losses
skills/harness-cost/SKILL.md      measuring and cutting agent cost
sync.ps1 / sync.sh                install into the global config, verify (-Check)
```

## Install (Windows, PowerShell 7)

```pwsh
git clone https://github.com/VadimAib/agent-ops "$env:USERPROFILE\agent-ops"
& "$env:USERPROFILE\agent-ops\sync.ps1"
& "$env:USERPROFILE\agent-ops\sync.ps1" -Check    # 0 = in sync, 1 = drift
```

An existing `AGENTS.md` without the `agent-ops` marker is never overwritten: our
version is placed next to it as `AGENTS.agent-ops.md` and reported.

## Notes

Every figure is a dated sample (2026-11-18) with the command that produced it,
not a promise — re-measure with the script in `skills/harness-cost`. The rule
file itself costs 440 extra prefix tokens per step (measured with the same
recipe). Windows-only: tested with pwsh 7.6.10 on Windows 10 (19045); `sync.sh`
was tested in WSL (bash 5.1.16). MIT.

# agent-ops

Global instructions and skills for a coding agent (OpenCode), installable by anyone.

Two rules shape the rest: **do not invent facts** ("no data" beats a guess) and
**measure instead of guessing**. Money is counted in the provider's currency,
because the UI may label it as another one.

```
AGENTS.md                         8 rules, 1 649 characters
skills/windows-console/SKILL.md   commands on Windows + pwsh without losses
skills/harness-cost/SKILL.md      how to measure and cut agent cost
sync.ps1 / sync.sh                install into the global config, verify (-Check)
```

## Install — Windows, PowerShell 7

```pwsh
git clone https://github.com/VadimAib/agent-ops "$env:USERPROFILE\agent-ops"
& "$env:USERPROFILE\agent-ops\sync.ps1"
& "$env:USERPROFILE\agent-ops\sync.ps1" -Check    # 0 = in sync, 1 = drift
```

An existing `AGENTS.md` without the `agent-ops` marker is never overwritten: our
version is placed next to it as `AGENTS.agent-ops.md` and reported.

## Notes

Every number is a dated sample (18.11.2026) with the command that produced it,
not a promise — re-measure with the script in `skills/harness-cost`. Windows-only:
tested with pwsh 7.6.10 on Windows 10 (19045). MIT.

---

## По-русски

Глобальные правила и скиллы для агента: без чужих путей, проектов и сумм.
Два принципа: **без выдумок** (нет подтверждения — «нет данных») и
**мерить, а не догадываться**. Деньги — в валюте провайдера.

Установка (Windows, PowerShell 7):

```pwsh
git clone https://github.com/VadimAib/agent-ops "$env:USERPROFILE\agent-ops"
& "$env:USERPROFILE\agent-ops\sync.ps1"
& "$env:USERPROFILE\agent-ops\sync.ps1" -Check    # 0 — совпадает, 1 — расхождение
```

`AGENTS.md` с чужим содержимым не перезаписывается: рядом появится
`AGENTS.agent-ops.md`.

Внутри: правила на 1 649 знаков (8 пунктов, +603 токена к префиксу шага — замер
18.11.2026), приёмы консоли Windows и методика замера стоимости. Числа в тексте —
примеры замера с датой и командой, а не обещание: свои считать тем же скриптом.
Проверено на pwsh 7.6.10, Windows 10 (19045). Лицензия MIT.

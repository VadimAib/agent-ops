---
name: windows-autostart
description: Windows autostart and background processes - auditing what starts at login (Run/RunOnce keys, Startup folder, scheduled tasks, services), the StartupApproved flag that Task Manager writes (2 = on, 3 = off, the entry itself stays), what needs UAC and what does not, and the pitfalls: msrdc.exe named "Remote Desktop" may be the WSLg client, not RDP; any wsl.exe call starts the distro and takes RAM; wsl -l -v prints UTF-16; Register-ScheduledTask -Force keeps old triggers; @($task.Triggers).Count is 1 even when empty. Load for "why does this start with Windows", "disable autostart but keep the entry", "what is this unfamiliar process", and before changing a service or a scheduled task.
---

# Windows autostart and background processes

## 1. Audit first, change second

Read-only picture, no admin rights needed:

```powershell
Get-CimInstance Win32_Service | Where-Object StartMode -eq 'Auto' |
    Select-Object Name, State, StartName, PathName
Get-ScheduledTask | Where-Object State -ne 'Disabled' |
    Select-Object TaskPath, TaskName, State
Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run'
Get-ItemProperty 'HKLM:\Software\Microsoft\Windows\CurrentVersion\Run'
Get-ChildItem "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup"
```

## 2. Four mechanisms, four different treatments

| Mechanism | Where to look | How to switch off | UAC |
|---|---|---|---|
| Service | `Win32_Service`, `StartMode = Auto` | `Set-Service X -StartupType Manual` + `Stop-Service X` | yes |
| `Run` / `RunOnce` entry | `HKCU`/`HKLM\...\CurrentVersion\Run` | value `3` in `...\Explorer\StartupApproved\Run` (`\Run32` for WOW6432Node); the entry stays | HKLM yes, HKCU no |
| Scheduled task | `Get-ScheduledTask` | `Disable-ScheduledTask` | other people's tasks: yes |
| Startup folder shortcut | `...\Start Menu\Programs\Startup` | value `3` in `StartupApproved\StartupFolder` | HKLM yes |

`Run` entries have no "manual start": Task Manager stores only an on/off flag.
`2` = enabled, `3` = disabled; test with `$v[0] -band 1`. Deleting the value or the
shortcut destroys the entry - that is not what "disable" means.

## 3. Order of changes

audit -> check whether it is already disabled -> **ask the human** what to remove,
and offer "leave it" -> apply by script through `Start-Process -Verb RunAs` with a
log file (the agent's own console has no admin rights) -> verify (process, port,
service state) -> write down what changed and how to roll back.

## 4. Pitfalls that already cost time

| Symptom | What it actually is |
|---|---|
| "Remote Desktop" (`msrdc.exe`) running although RDP is off | check the parent and the command line first: with parent `wslhost` and `/wslg ... wslg.rdp` it is the **WSLg client**, not RDP. `Stop-Process` is useless - WSLg restarts it in ~2 s. Turn off `guiApplications=false` in `%USERPROFILE%\.wslconfig`, then `wsl --shutdown` |
| "checked the state" - and a WSL-based service came up and took RAM | every `wsl.exe` call starts the distro and keeps it alive. Read state without WSL: `Get-Process vmmem`, `Get-Service` |
| `wsl -l -v` prints `U b u n t u - 2 2 . 0 4` | the output is UTF-16: do not parse it, or convert first |
| `Register-ScheduledTask -Force` without `-Trigger` kept the old triggers | empty triggers come only from registering **without** the `-Trigger` parameter; verify with `Export-ScheduledTask` -> `<Triggers />` |
| `@($task.Triggers).Count` equals 1 when the triggers are empty | PowerShell counts the array itself; use `($task.Triggers \| Measure-Object).Count` |
| `Access is denied` on a protected object | normal, not a fault: tasks are changed by a separate script through UAC, ACLs are left alone |
| service stopped but its process is still there | `Stop-Service` does not kill third-party child processes: check `Get-Process` by name |

## 5. Do not touch what is not yours

A process name proves nothing. Find the owner (path, install date, parent) and then
ask the human, offering "leave it". A local database server may belong to another
product while the project's own database runs in a container.

## 6. Rollback

Keep the previous value of every setting you change (registry export, service
StartMode, task state) and write the reverse command next to it before applying.

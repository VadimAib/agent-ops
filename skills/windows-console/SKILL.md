---
name: windows-console
description: Windows and pwsh commands without losing output - "????"/UnicodeEncodeError, silent pipelines, rejected commands (invalid-structure), WSL versus Git Bash, quoting.
---

# windows-console — commands on Windows without losses

Verified 2026-11-18: `$PSVersionTable.PSVersion` → 7.6.10, `python --version` →
3.14.3, `wsl --version` → WSL 3.0.5.0. Other versions may behave differently:
each section ends with a check command, not a promise.

## 0. What to do when something fails

1. Read the whole error: it almost always names the entity (encoding, parser,
   missing file), not just "the command did not work".
2. Check whether anything ran at all: `$LASTEXITCODE`, `$?`, does the file exist.
3. Narrow it down to one command without a pipeline — the cause becomes visible.
4. Do not retry the same string "once more": a parser rejection will repeat,
   and side effects (a written file) may already have happened.

## 1. Encodings: `????` and UnicodeEncodeError

**Symptom.** Python prints `????`, `�`, or dies with `UnicodeEncodeError:
'charmap' codec can't encode characters`. The file it writes is fine.

**Cause.** The child process encodes stdout with the console code page
(usually 1251/866; on Windows 11 with pwsh 7 and python 3.14 it is **1252**, so
the message reads `'charmap' codec can't encode … cp1252`), not UTF-8.

**Fix.** Set the encoding before starting python, in the same session:

```pwsh
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'          # same for file operations inside python
[Console]::OutputEncoding = [Text.Encoding]::UTF8   # how the console itself reads
python .\script.py
```

**Check.**

```pwsh
$env:PYTHONIOENCODING='utf-8'; python -c "print('日本語')"
```

If you still see `????`, the variable did not reach the process (Task Scheduler,
`Start-Process`, another shell): pass it explicitly.

**Separate case: `????` produced by PowerShell itself.** If `Write-Output` or
`Write-Host` loses non-ASCII text, the console code page is to blame (437 is the
default on English Windows). Check and work around:

```pwsh
[Console]::OutputEncoding.WebName     # ibm437 — cannot encode CJK
[Console]::OutputEncoding.GetBytes('日') -join ','   # 63 — replacement character
[Console]::OutputEncoding = [Text.Encoding]::UTF8
[Console]::Out.WriteLine('日本語')    # writes bytes directly, bypassing the host
```

The file itself stays correct: `[IO.File]::ReadAllBytes('.\out.txt')[0..2]` gives
`230,151,165` — UTF-8 for "日". Only the screen output breaks. `chcp 65001` from
inside the session does not help: the host binds its encoding at start-up.
Verified 2026-11-18, pwsh 7.6.10, `ibm437`.

## 2. The silent pipeline: `Select-String` is not the same as a file plus `Get-Content`

**Symptom.** `Get-Content x.log | Select-String 'error'` returns 0 rows although
the text is there. Or it returns objects you cannot pass on as text.

**Two causes that add up:**

- `Select-String` emits `MatchInfo` objects (properties `.Line`, `.LineNumber`),
  not strings. A pipeline receives the object; the console shows formatting.
- If the file is in another encoding (UTF-16 from a native tool, 1251 from an old
  one), a non-ASCII pattern will not match — silently, with no error.

**Fix.** Determine the encoding from the first bytes, then read with an explicit
encoding; capture native output into a file and read the file.

```pwsh
# 1. which encoding: 255,254 = UTF-16 LE, 239,187,191 = UTF-8 BOM, otherwise guess
[IO.File]::ReadAllBytes('.\out.txt')[0..3] -join ','

# 2. write to a file instead of a pipeline
& native.exe 2>&1 | Tee-Object -FilePath .\out.txt
Get-Content .\out.txt -Encoding utf8

# 3. if you need to search objects, take the line explicitly
Get-Content .\out.txt -Encoding utf8 | Select-String 'error' | ForEach-Object Line
```

**Rule.** A pipeline that "found nothing" is a statement about the encoding, not
about the content. `Get-Content -Encoding` first, `Select-String` second.

**Check.** Create a UTF-16 file and search it for non-ASCII text without
`-Encoding`: no matches; with `-Encoding unicode`: matches.

## 3. The strict command scanner: `invalid-structure`

**Symptom.** Instead of running, you get
`Portable shell scanner cannot analyze command: invalid-structure`. The command
never started; its exit code is meaningless.

**Cause.** The scanner (a wrapper around the shell) parses the line formally
instead of executing it. It is broken by mixed nested quotes, multi-line
constructs, method chains inside a pipeline (`$t.Replace(...)`,
`($x -split 'a')[0]` as an argument), `--%`, unbalanced brackets, a heredoc on
one line.

**Fix — do not fight the parser, take the complexity out of the command line:**

```pwsh
$code = @'
# any complex logic, multi-line, with quotes
'@
$p = Join-Path $env:TEMP 'task.ps1'
$code | Out-File -FilePath $p -Encoding utf8
& $p
```

- Edit files with an `edit` tool, not with `$text.Replace('a','b')` on the
  command line: an in-place replacement is the most common source of
  `invalid-structure`, and it trashes the file if it fails.
- Break a long command into simple calls: one command, one operation.
- If something was already written before the rejection, check the file: part of
  the line may have run before the failure point.

**Check.** The complex string should produce `invalid-structure`; the same text
saved to a `.ps1` via `Out-File` should run.

## 4. `bash` is WSL or Git Bash, and they are different

**Symptom.** A script works for one person and fails for another: wrong `bash`,
wrong paths, wrong line endings.

**Tell them apart.**

```pwsh
Get-Command bash -All | Select-Object -ExpandProperty Source
```

- `C:\Windows\system32\bash.exe` (and the `...\WindowsApps\bash.exe` stub) — **WSL**.
- `%ProgramFiles%\Git\bin\bash.exe` or `%LOCALAPPDATA%\Programs\Git\bin\bash.exe` —
  **Git Bash** (if installed; a clean Windows does not have it).

Second sign — the kernel:

```pwsh
bash -c 'uname -s -r'
# WSL:      Linux ... microsoft-standard-WSL2
# Git Bash: MINGW64_NT-10.0 ...
```

**Differences that break scripts:**

| | WSL | Git Bash |
|---|---|---|
| Path to drive C: | `/mnt/c/...` | `/c/...` |
| `wslpath` | present | absent |
| `cmd.exe`, `powershell.exe` | available | available |
| Home directory | its own (Linux) | `%USERPROFILE%` |
| Line endings | needs LF | LF; CRLF breaks the shebang |

**Fix.** Name the interpreter explicitly in instructions (`wsl bash -lc '...'` or
`& "$env:ProgramFiles\Git\bin\bash.exe" -lc '...'`), never bare `bash`. Store
scripts with LF: `.gitattributes` → `*.sh text eol=lf`.

**Check.** `bash -c 'uname -s'` must answer what you expect.

## 5. `wsl -l -v` prints UTF-16 and a pipeline loses it

**Symptom.** `wsl -l -v | Select-String 'Ubuntu'` finds nothing; the output shows
letters spaced out (`N A M E`), with NUL characters in the string.

**Cause.** `wsl.exe` writes the list as UTF-16 LE, while PowerShell reads the
bytes as a single-byte encoding: ASCII character + NUL per character.
`Select-String` compares against something that is not there.

**Fix.** Turn on `wsl`'s own UTF-8 mode for the call:

```pwsh
$env:WSL_UTF8 = '1'
wsl -l -v
```

The same applies to `wsl --version`.

**Check.** With `WSL_UTF8=1` the output of `wsl -l -v` is plain text without NULs
(verified 2026-11-18 on WSL 3.0.5.0).

## 6. Quotes, spaces and paths

```pwsh
& 'C:\Program Files\App\app.exe' --flag 'value with space'   # call by path
Get-Content -LiteralPath '.\file [1].txt'                    # brackets are not a pattern
```

- A path with spaces goes in quotes and through `&`; without `&` the string will
  not start a program.
- `-LiteralPath` instead of `-Path` when the name contains `[`, `]`, `*`, `?`.
- A path ending in `\` escapes the closing quote: `"C:\dir\"` is an error. Write
  `C:\dir` or `C:/dir`.
- `~` and `%USERPROFILE%` are expanded by pwsh (`$env:USERPROFILE`), but not
  inside single quotes.
- `--%` stops PowerShell parsing — only for native programs, and only when
  nothing else works.

## 7. Exit codes

| What to check | When |
|---|---|
| `$LASTEXITCODE` | after a native program (`git`, `python`, `node`) |
| `$?` | after a cmdlet (but with the default `-ErrorAction` it is soft) |
| `try/catch` + `-ErrorAction Stop` | the cmdlet must fail instead of writing to the error stream |

```pwsh
git status
if ($LASTEXITCODE -ne 0) { throw "git status: $LASTEXITCODE" }
```

- A native program with a non-zero code does **not** throw: check the code yourself.
- In a pipeline `$LASTEXITCODE` is from the last native command, not from the
  first one that failed.
- pwsh 7.3+: `$PSNativeCommandUseErrorActionPreference = $true` makes native
  failures respect `$ErrorActionPreference`.
- End a script explicitly: `exit 0` / `exit 1`. A script that just falls off the
  end is 0, even if everything inside broke.

**Check.** `cmd /c exit 3; $LASTEXITCODE` → `3`.

## Checklist before you run anything

- [ ] Non-ASCII output: `PYTHONIOENCODING`/`OutputEncoding` are set.
- [ ] Text is searched in a file with explicit `-Encoding`, not through a pipeline.
- [ ] Complex logic lives in a `.ps1`, not on one line.
- [ ] `bash` is named explicitly (WSL or Git Bash).
- [ ] Paths are quoted, `-LiteralPath` where needed.
- [ ] `$LASTEXITCODE` is checked wherever a native program was called.

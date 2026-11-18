#Requires -Version 7.0
<#
.SYNOPSIS
    Разворачивает agent-ops в глобальный конфиг OpenCode и сверяет установку.

.DESCRIPTION
    Копирует AGENTS.md и skills\<имя>\SKILL.md в каталог глобального конфига.
    AGENTS.md с чужим содержимым (без маркера agent-ops) не перезаписывается:
    рядом кладётся AGENTS.agent-ops.md и печатается предупреждение.

.PARAMETER Check
    Ничего не менять. Код 0 — установка совпадает с репозиторием, код 1 —
    есть расхождение или отсутствующий файл.

.PARAMETER Target
    Каталог конфига. По умолчанию %USERPROFILE%\.config\opencode.

.PARAMETER Force
    Перезаписать AGENTS.md, даже если маркера в нём нет.

.EXAMPLE
    .\sync.ps1
    .\sync.ps1 -Check
    .\sync.ps1 -Check -Target (Join-Path $env:TEMP 'cfg-test')
#>
[CmdletBinding()]
param(
    [switch]$Check,
    [string]$Target = (Join-Path $env:USERPROFILE '.config\opencode'),
    [switch]$Force
)

$ErrorActionPreference = 'Stop'
$repo = $PSScriptRoot
$fail = 0

# Кодовая страница консоли без кириллицы (437, 1252) печатает «????»:
# Write-Host кодирует через кодировку хоста, и изнутри сессии её не сменить.
# В таком случае (и при перенаправленном выводе) пишем в stdout напрямую UTF-8.
$script:rawOut = $true
try {
    if (([Console]::OutputEncoding.GetBytes('Я') -join ',') -ne '63') { $script:rawOut = $false }
    if ([Console]::IsOutputRedirected) {
        [Console]::OutputEncoding = [Text.Encoding]::UTF8
        $script:rawOut = $true
    }
}
catch { $script:rawOut = $true }

function Say {
    param(
        [Parameter(Position = 0)][string]$Object = '',
        [Parameter(Position = 1)][string]$ForegroundColor = 'Gray'
    )
    if ($script:rawOut) { [Console]::Out.WriteLine($Object) }
    else { Write-Host $Object -ForegroundColor $ForegroundColor }
}

function Test-SameFile {
    param([string]$A, [string]$B)
    if (-not (Test-Path -LiteralPath $A) -or -not (Test-Path -LiteralPath $B)) {
        return $false
    }
    $x = [IO.File]::ReadAllBytes($A)
    $y = [IO.File]::ReadAllBytes($B)
    if ($x.Length -ne $y.Length) { return $false }
    for ($i = 0; $i -lt $x.Length; $i++) {
        if ($x[$i] -ne $y[$i]) { return $false }
    }
    return $true
}

# --- проверка самого набора: правила должны остаться правилами ---------------
$agentsSrc = Join-Path $repo 'AGENTS.md'
if (-not (Test-Path -LiteralPath $agentsSrc)) {
    Say "FAIL  нет $agentsSrc" 'Red'
    exit 1
}
$agentsText = [IO.File]::ReadAllText($agentsSrc)
$chars = $agentsText.Length
$points = ([regex]::Matches($agentsText, '(?m)^\d+\. ')).Count
Say ("AGENTS.md: {0} знаков, {1} пунктов" -f $chars, $points)
if ($chars -gt 2000) {
    Say 'FAIL  AGENTS.md длиннее 2 000 знаков' 'Red'
    $fail = 1
}
if ($points -lt 6 -or $points -gt 10) {
    Say 'FAIL  в AGENTS.md должно быть 6-10 пунктов' 'Red'
    $fail = 1
}

# --- что и куда -------------------------------------------------------------
$items = @([pscustomobject]@{
        Rel   = 'AGENTS.md'
        Src   = $agentsSrc
        Dst   = (Join-Path $Target 'AGENTS.md')
        Guard = $true
    })
$skillsDir = Join-Path $repo 'skills'
if (Test-Path -LiteralPath $skillsDir) {
    foreach ($d in Get-ChildItem -LiteralPath $skillsDir -Directory) {
        $items += [pscustomobject]@{
            Rel   = ('skills/{0}/SKILL.md' -f $d.Name)
            Src   = (Join-Path $d.FullName 'SKILL.md')
            Dst   = (Join-Path (Join-Path $Target 'skills') (Join-Path $d.Name 'SKILL.md'))
            Guard = $false
        }
    }
}

if ($Check) {
    Say ("Сверка с {0}" -f $Target)
    foreach ($it in $items) {
        if (Test-SameFile $it.Src $it.Dst) {
            Say ("OK      {0}" -f $it.Rel) 'Green'
        }
        else {
            Say ("DRIFT   {0}" -f $it.Rel) 'Yellow'
            $fail = 1
        }
    }
    if ($fail -eq 0) { Say 'Установка совпадает с репозиторием.' 'Green' }
    else { Say 'Есть расхождения: запустите sync.ps1 без -Check.' 'Yellow' }
    exit $fail
}

# --- установка --------------------------------------------------------------
Say ("Установка в {0}" -f $Target)
foreach ($it in $items) {
    if (-not (Test-Path -LiteralPath $it.Src)) {
        Say ("FAIL  нет {0}" -f $it.Rel) 'Red'
        $fail = 1
        continue
    }
    $dstDir = Split-Path -Parent $it.Dst
    if (-not (Test-Path -LiteralPath $dstDir)) {
        New-Item -ItemType Directory -Path $dstDir -Force | Out-Null
    }

    if ($it.Guard -and (Test-Path -LiteralPath $it.Dst) -and -not $Force) {
        $old = [IO.File]::ReadAllText($it.Dst)
        $head = $old.Substring(0, [Math]::Min(200, $old.Length))
        if ($head -notmatch '(?i)agent[- ]?op') {
            $alt = Join-Path $dstDir 'AGENTS.agent-ops.md'
            Copy-Item -LiteralPath $it.Src -Destination $alt -Force
            Say ("ЕСТЬ    {0} не от agent-ops — не тронут; наш вариант: AGENTS.agent-ops.md" -f $it.Rel) 'Yellow'
            $fail = 1
            continue
        }
    }

    Copy-Item -LiteralPath $it.Src -Destination $it.Dst -Force
    Say ("СТАВЛЮ  {0}" -f $it.Rel) 'Green'
}

Say 'Готово. Проверка: .\sync.ps1 -Check'
exit $fail

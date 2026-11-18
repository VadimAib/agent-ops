#Requires -Version 7.0
<#
.SYNOPSIS
    Installs agent-ops into the global OpenCode config and verifies the install.

.DESCRIPTION
    Copies AGENTS.md and skills\<name>\SKILL.md into the global config directory.
    An AGENTS.md that is not ours (no agent-ops marker) is never overwritten:
    ours is placed next to it as AGENTS.agent-ops.md and reported.

.PARAMETER Check
    Change nothing. Exit 0 when the install matches the repo, exit 1 when there
    is a difference or a missing file.

.PARAMETER Target
    Config directory. Defaults to %USERPROFILE%\.config\opencode.

.PARAMETER Force
    Overwrite AGENTS.md even when it has no marker.

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

# A console code page without the needed glyphs (437, 1252) prints "????":
# Write-Host encodes through the host code page and it cannot be changed from
# inside a session. Then (and when output is redirected) write to stdout as UTF-8.
$script:rawOut = $true
try {
    if (([Console]::OutputEncoding.GetBytes('日') -join ',') -ne '63') { $script:rawOut = $false }
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

# --- the set checks itself: the rules must stay rules ------------------------
$agentsSrc = Join-Path $repo 'AGENTS.md'
if (-not (Test-Path -LiteralPath $agentsSrc)) {
    Say "FAIL  missing $agentsSrc" 'Red'
    exit 1
}
$agentsText = [IO.File]::ReadAllText($agentsSrc)
$chars = $agentsText.Length
$points = ([regex]::Matches($agentsText, '(?m)^\d+\. ')).Count
Say ("AGENTS.md: {0} chars, {1} points" -f $chars, $points)
if ($chars -gt 2000) {
    Say 'FAIL  AGENTS.md is longer than 2000 characters' 'Red'
    $fail = 1
}
if ($points -lt 6 -or $points -gt 10) {
    Say 'FAIL  AGENTS.md must have 6-10 points' 'Red'
    $fail = 1
}

# --- what goes where --------------------------------------------------------
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
    Say ("Checking against {0}" -f $Target)
    foreach ($it in $items) {
        if (Test-SameFile $it.Src $it.Dst) {
            Say ("OK      {0}" -f $it.Rel) 'Green'
        }
        else {
            Say ("DRIFT   {0}" -f $it.Rel) 'Yellow'
            $fail = 1
        }
    }
    if ($fail -eq 0) { Say 'Install matches the repo.' 'Green' }
    else { Say 'Differences found: run sync.ps1 without -Check.' 'Yellow' }
    exit $fail
}

# --- install ----------------------------------------------------------------
Say ("Installing into {0}" -f $Target)
foreach ($it in $items) {
    if (-not (Test-Path -LiteralPath $it.Src)) {
        Say ("FAIL  missing {0}" -f $it.Rel) 'Red'
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
            Say ("EXISTS  {0} is not from agent-ops — left untouched; ours: AGENTS.agent-ops.md" -f $it.Rel) 'Yellow'
            $fail = 1
            continue
        }
    }

    Copy-Item -LiteralPath $it.Src -Destination $it.Dst -Force
    Say ("WRITE   {0}" -f $it.Rel) 'Green'
}

Say 'Done. Verify: .\sync.ps1 -Check'
exit $fail

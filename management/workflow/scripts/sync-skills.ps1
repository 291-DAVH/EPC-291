# sync-skills.ps1
# Copies framework skills (.claude/skills/*/SKILL.md) to the Claude account-level
# skills cache (AppData), keeping both in sync.
#
# Usage:
#   .\sync-skills.ps1              # framework → account (default)
#   .\sync-skills.ps1 -Direction framework_to_account
#   .\sync-skills.ps1 -Direction account_to_framework
#   .\sync-skills.ps1 -DryRun      # preview without copying
#
# The account-level skills path contains session-specific UUIDs. This script
# finds the correct path automatically by searching for SKILL.md files under
# the skills-plugin directory.

param(
    [ValidateSet("framework_to_account", "account_to_framework")]
    [string]$Direction = "framework_to_account",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

# Paths
$FrameworkSkillsRoot = Join-Path $PSScriptRoot "..\skills"
$AppDataSkillsBase   = "$env:APPDATA\Claude\local-agent-mode-sessions\skills-plugin"

# Resolve absolute path for framework skills
$FrameworkSkillsRoot = (Resolve-Path $FrameworkSkillsRoot).Path

# Discover account skills root by finding any existing SKILL.md under skills-plugin
# Structure: skills-plugin\<uuid1>\<uuid2>\skills\<skill-name>\SKILL.md
$AccountSkillsRoot = $null
$existing = Get-ChildItem -Path $AppDataSkillsBase -Recurse -Filter "SKILL.md" -ErrorAction SilentlyContinue |
    Select-Object -First 1
if ($existing) {
    # skills\ parent is two levels up from SKILL.md → skill-name → skills
    $AccountSkillsRoot = $existing.Directory.Parent.FullName
} else {
    # No existing skills found — try to construct the path from the most recently
    # modified uuid pair under skills-plugin
    $uuid1 = Get-ChildItem -Path $AppDataSkillsBase -Directory -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($uuid1) {
        $uuid2 = Get-ChildItem -Path $uuid1.FullName -Directory -ErrorAction SilentlyContinue |
            Sort-Object LastWriteTime -Descending | Select-Object -First 1
        if ($uuid2) {
            $AccountSkillsRoot = Join-Path $uuid2.FullName "skills"
        }
    }
}

if (-not $AccountSkillsRoot) {
    Write-Error "Could not find the Claude account skills directory under:`n  $AppDataSkillsBase`nMake sure Claude desktop app has run at least once."
    exit 1
}

Write-Host "Framework skills : $FrameworkSkillsRoot"
Write-Host "Account skills   : $AccountSkillsRoot"
Write-Host "Direction        : $Direction"
if ($DryRun) { Write-Host "[DRY RUN — no files will be written]" -ForegroundColor Yellow }
Write-Host ""

function Sync-SkillFile {
    param([string]$SourceFile, [string]$DestFile)
    $destDir = Split-Path $DestFile -Parent
    if (-not (Test-Path $destDir)) {
        if (-not $DryRun) { New-Item -ItemType Directory -Path $destDir -Force | Out-Null }
        Write-Host "  [NEW DIR] $destDir"
    }
    if ($DryRun) {
        Write-Host "  [COPY]    $SourceFile → $DestFile"
    } else {
        Copy-Item -Path $SourceFile -Destination $DestFile -Force
        Write-Host "  [OK]      $(Split-Path $SourceFile -Parent | Split-Path -Leaf)\SKILL.md"
    }
}

# Collect framework skill names
$FrameworkSkills = Get-ChildItem -Path $FrameworkSkillsRoot -Directory |
    Where-Object { Test-Path (Join-Path $_.FullName "SKILL.md") }

# Collect account skill names
$AccountSkills = @()
if (Test-Path $AccountSkillsRoot) {
    $AccountSkills = Get-ChildItem -Path $AccountSkillsRoot -Directory -ErrorAction SilentlyContinue |
        Where-Object { Test-Path (Join-Path $_.FullName "SKILL.md") }
}

if ($Direction -eq "framework_to_account") {
    Write-Host "Syncing $($FrameworkSkills.Count) framework skills → account..."
    foreach ($skill in $FrameworkSkills) {
        $src  = Join-Path $skill.FullName "SKILL.md"
        $dest = Join-Path $AccountSkillsRoot "$($skill.Name)\SKILL.md"
        Sync-SkillFile -SourceFile $src -DestFile $dest
    }
    # Report account skills not in framework (won't be deleted — just flagged)
    $frameworkNames = $FrameworkSkills | Select-Object -ExpandProperty Name
    $extra = $AccountSkills | Where-Object { $_.Name -notin $frameworkNames }
    if ($extra) {
        Write-Host ""
        Write-Host "Account skills NOT in framework (kept as-is):" -ForegroundColor Yellow
        $extra | ForEach-Object { Write-Host "  $($_.Name)" }
    }
} else {
    Write-Host "Syncing $($AccountSkills.Count) account skills → framework..."
    foreach ($skill in $AccountSkills) {
        $src  = Join-Path $skill.FullName "SKILL.md"
        $dest = Join-Path $FrameworkSkillsRoot "$($skill.Name)\SKILL.md"
        Sync-SkillFile -SourceFile $src -DestFile $dest
    }
}

Write-Host ""
Write-Host "Done." -ForegroundColor Green

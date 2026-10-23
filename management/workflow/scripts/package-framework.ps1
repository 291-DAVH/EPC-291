# package-framework.ps1
# Empaqueta el framework para compartir con otro usuario, excluyendo los datos
# de entrenamiento de las skills (knowledge, learning/inventory.json, cache, memory).
#
# El destinatario recibe la estructura completa de las skills pero sin el
# conocimiento ya estudiado — debe cargar sus propios archivos y ejecutar
# skill learn para entrenar sus skills desde cero.
#
# Uso:
#   .\package-framework.ps1 -Destination "C:\Ruta\Destino"
#   .\package-framework.ps1 -Destination "C:\Ruta\Destino" -DryRun
#   .\package-framework.ps1 -Destination "C:\Ruta\Destino" -SkipGitFiles
#
# Qué se excluye:
#   .claude/skills/*/knowledge/**    (archivos de entrenamiento: PDFs, SVGs, etc.)
#   .claude/skills/*/learning/inventory.json   (registro de qué fue estudiado)
#   .claude/skills/*/cache/**        (caché temporal de aprendizaje)
#   .claude/skills/*/memory/**       (resúmenes generados automáticamente)
#
# Qué se preserva (estructura vacía):
#   .claude/skills/*/knowledge/      (carpeta vacía — el destinatario deposita sus archivos)
#   .claude/skills/*/learning/       (carpeta vacía)
#   .claude/skills/*/cache/          (carpeta vacía)
#   .claude/skills/*/memory/         (carpeta vacía)

param(
    [Parameter(Mandatory = $true)]
    [string]$Destination,
    [switch]$DryRun,
    [switch]$SkipGitFiles
)

$ErrorActionPreference = "Stop"

$Source = Split-Path $PSScriptRoot -Parent | Split-Path -Parent
$Source = (Resolve-Path $Source).Path

Write-Host "Framework source : $Source"
Write-Host "Destination      : $Destination"
if ($DryRun)      { Write-Host "[DRY RUN — no files will be written]" -ForegroundColor Yellow }
Write-Host ""

# Patterns that identify training-data paths (relative to source root)
# These files/dirs are EXCLUDED from the copy
$TrainingExcludes = @(
    [regex]::new('[\\/]\.claude[\\/]skills[\\/][^[\\/]+[\\/]knowledge[\\/].+'),
    [regex]::new('[\\/]\.claude[\\/]skills[\\/][^[\\/]+[\\/]learning[\\/]inventory\.json$'),
    [regex]::new('[\\/]\.claude[\\/]skills[\\/][^[\\/]+[\\/]cache[\\/].+'),
    [regex]::new('[\\/]\.claude[\\/]skills[\\/][^[\\/]+[\\/]memory[\\/].+')
)

# Patterns for files always excluded (OS/editor noise)
$AlwaysExclude = @('*.tmp', '*.bak', '*~', '.DS_Store', 'Thumbs.db', '~$*')

# Git-related files (excluded with -SkipGitFiles)
$GitExclude = @('.git')

function ShouldExclude([string]$RelPath) {
    foreach ($pattern in $TrainingExcludes) {
        if ($pattern.IsMatch($RelPath)) { return $true }
    }
    $leaf = Split-Path $RelPath -Leaf
    foreach ($pattern in $AlwaysExclude) {
        if ($leaf -like $pattern) { return $true }
    }
    if ($SkipGitFiles) {
        foreach ($name in $GitExclude) {
            if ($RelPath -match "(^|[\\/])$([regex]::Escape($name))([\\/]|$)") { return $true }
        }
    }
    return $false
}

$copied = 0
$skipped = 0
$created = 0

# Walk all items under Source
Get-ChildItem -Path $Source -Recurse -Force | ForEach-Object {
    $item    = $_
    $relPath = $item.FullName.Substring($Source.Length)
    $destPath = Join-Path $Destination $relPath

    if (ShouldExclude $relPath) {
        $skipped++
        return
    }

    if ($item.PSIsContainer) {
        if (-not (Test-Path $destPath)) {
            if (-not $DryRun) { New-Item -ItemType Directory -Path $destPath -Force | Out-Null }
            $created++
        }
    } else {
        $destDir = Split-Path $destPath -Parent
        if (-not (Test-Path $destDir)) {
            if (-not $DryRun) { New-Item -ItemType Directory -Path $destDir -Force | Out-Null }
        }
        if ($DryRun) {
            Write-Host "  [COPY] $relPath"
        } else {
            Copy-Item -Path $item.FullName -Destination $destPath -Force
        }
        $copied++
    }
}

# Ensure skill subdirectory skeletons exist at destination (empty, ready for content)
$SkillDirsToEnsure = @('knowledge', 'learning', 'cache', 'memory')
$skillsRoot = Join-Path $Destination ".claude\skills"
if (Test-Path (Join-Path $Source ".claude\skills")) {
    Get-ChildItem -Path (Join-Path $Source ".claude\skills") -Directory | ForEach-Object {
        $skillName = $_.Name
        foreach ($subDir in $SkillDirsToEnsure) {
            $target = Join-Path $skillsRoot "$skillName\$subDir"
            if (-not (Test-Path $target)) {
                if (-not $DryRun) { New-Item -ItemType Directory -Path $target -Force | Out-Null }
                Write-Host "  [SKELETON] .claude\skills\$skillName\$subDir\" -ForegroundColor DarkGray
            }
        }
    }
}

Write-Host ""
Write-Host "Done." -ForegroundColor Green
Write-Host "  Directories created : $created"
Write-Host "  Files copied        : $copied"
Write-Host "  Items skipped       : $skipped (training data excluded)"
Write-Host ""
Write-Host "The recipient must run 'skill learn' for each skill after loading their own"
Write-Host "training files into .claude/skills/<skill>/knowledge/."

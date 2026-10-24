# Copia de respaldo de local/ (normas, planos de terceros, legacy: material que no se puede reconstruir y no vive en git).
#   .\tools\dev\backup_local.ps1 -Destino D:\respaldos          carpeta fuera del repositorio (unidad de red o nube privada sincronizada)
# Genera <Destino>\epc-local-AAAAMMDD-HHMMSS.zip y conserva las ultimas -Conservar copias. No toca local/.
param(
    [Parameter(Mandatory = $true)][string]$Destino,
    [int]$Conservar = 5
)
$repo = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$local = Join-Path $repo "local"
if (-not (Test-Path $local)) { "no existe $local"; exit 1 }
if ((Resolve-Path $Destino -ErrorAction SilentlyContinue) -and ((Resolve-Path $Destino).Path.StartsWith($repo))) { "el destino debe estar fuera del repositorio"; exit 1 }
New-Item -ItemType Directory -Force $Destino | Out-Null
$zip = Join-Path $Destino ("epc-local-" + (Get-Date -Format "yyyyMMdd-HHmmss") + ".zip")
Compress-Archive -Path (Join-Path $local "*") -DestinationPath $zip -CompressionLevel Optimal
"respaldo: $zip"
Get-ChildItem $Destino -Filter "epc-local-*.zip" | Sort-Object LastWriteTime -Descending | Select-Object -Skip $Conservar | Remove-Item -Force

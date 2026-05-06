$ErrorActionPreference = "Stop"
$root = git rev-parse --show-toplevel
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $root "tools\validate-skill.ps1")
exit $LASTEXITCODE

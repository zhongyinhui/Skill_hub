$ErrorActionPreference = "Stop"
$root = git rev-parse --show-toplevel
powershell -ExecutionPolicy Bypass -File (Join-Path $root "tools\validate-skill.ps1")


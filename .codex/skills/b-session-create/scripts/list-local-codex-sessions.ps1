param(
    [string]$CodexHome = "",

    [string]$ThreadId = "",

    [int]$Limit = 20
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

if ($Limit -lt 1 -or $Limit -gt 200) {
    throw "Limit must be between 1 and 200."
}

if ([string]::IsNullOrWhiteSpace($CodexHome)) {
    if (-not [string]::IsNullOrWhiteSpace($env:CODEX_HOME)) {
        $CodexHome = $env:CODEX_HOME
    }
    else {
        $CodexHome = Join-Path $env:USERPROFILE ".codex"
    }
}

$sessionsRoot = Join-Path $CodexHome "sessions"
if (-not (Test-Path -LiteralPath $sessionsRoot)) {
    throw "Codex sessions root not found: $sessionsRoot"
}

$files = Get-ChildItem -LiteralPath $sessionsRoot -Recurse -File -Filter "*.jsonl" -ErrorAction SilentlyContinue

if (-not [string]::IsNullOrWhiteSpace($ThreadId)) {
    $files = $files | Where-Object {
        $_.Name -like "*$ThreadId*" -or
        (Select-String -LiteralPath $_.FullName -Pattern $ThreadId -SimpleMatch -Quiet -ErrorAction SilentlyContinue)
    }
}

$items = @(
    $files |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First $Limit |
        ForEach-Object {
            [ordered]@{
                path = $_.FullName
                name = $_.Name
                last_write_time = $_.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss")
                length = $_.Length
                source_ref = "local-codex-session-jsonl:$($_.FullName)"
            }
        }
)

[ordered]@{
    codex_home = (Resolve-Path -LiteralPath $CodexHome).Path
    sessions_root = (Resolve-Path -LiteralPath $sessionsRoot).Path
    thread_filter = $ThreadId
    count = $items.Count
    sessions = $items
} | ConvertTo-Json -Depth 6

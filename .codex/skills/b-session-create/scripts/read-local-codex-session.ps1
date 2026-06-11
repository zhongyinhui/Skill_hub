param(
    [Parameter(Mandatory = $true)]
    [string]$SessionPath,

    [int]$TailEvents = 20
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

if (-not (Test-Path -LiteralPath $SessionPath)) {
    throw "SessionPath does not exist: $SessionPath"
}
if ($TailEvents -lt 0 -or $TailEvents -gt 200) {
    throw "TailEvents must be between 0 and 200."
}

$resolvedPath = (Resolve-Path -LiteralPath $SessionPath).Path
$fileInfo = Get-Item -LiteralPath $resolvedPath
$tail = New-Object System.Collections.Generic.Queue[object]

$lineCount = 0
$parseErrors = 0
$sessionMeta = $null
$firstTimestamp = $null
$lastTimestamp = $null

$stream = [System.IO.File]::Open($resolvedPath, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
$reader = New-Object System.IO.StreamReader($stream, [System.Text.Encoding]::UTF8)
try {
    while (($line = $reader.ReadLine()) -ne $null) {
        $lineCount++
        if ([string]::IsNullOrWhiteSpace($line)) {
            continue
        }

        try {
            $obj = $line | ConvertFrom-Json
        }
        catch {
            $parseErrors++
            continue
        }

        if ($obj.timestamp) {
            if ($null -eq $firstTimestamp) {
                $firstTimestamp = [string]$obj.timestamp
            }
            $lastTimestamp = [string]$obj.timestamp
        }

        if ($obj.type -eq "session_meta" -and $obj.payload) {
            $sessionMeta = $obj.payload
        }

        if ($TailEvents -gt 0) {
            $event = [ordered]@{
                line = $lineCount
                timestamp = [string]$obj.timestamp
                type = [string]$obj.type
            }
            if ($obj.payload -and $obj.payload.role) {
                $event.role = [string]$obj.payload.role
            }
            if ($tail.Count -ge $TailEvents) {
                [void]$tail.Dequeue()
            }
            $tail.Enqueue($event)
        }
    }
}
finally {
    $reader.Close()
    $stream.Close()
}

$codexSessionId = ""
$codexCreatedAt = ""
$codexCwd = ""
$originator = ""
$cliVersion = ""
if ($sessionMeta) {
    $codexSessionId = [string]$sessionMeta.id
    $codexCreatedAt = [string]$sessionMeta.timestamp
    $codexCwd = [string]$sessionMeta.cwd
    $originator = [string]$sessionMeta.originator
    $cliVersion = [string]$sessionMeta.cli_version
}

if ([string]::IsNullOrWhiteSpace($codexSessionId)) {
    $codexSourceRef = "local-codex-session-jsonl:$resolvedPath"
}
else {
    $codexSourceRef = "codex-session:$codexSessionId"
}

[ordered]@{
    codex_session_ref = $codexSourceRef
    codex_session_id = $codexSessionId
    codex_created_at = $codexCreatedAt
    codex_cwd = $codexCwd
    originator = $originator
    cli_version = $cliVersion
    local_jsonl_path = $resolvedPath
    file_last_write_time = $fileInfo.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss")
    file_length = $fileInfo.Length
    event_count = $lineCount
    parse_errors = $parseErrors
    first_event_timestamp = $firstTimestamp
    last_event_timestamp = $lastTimestamp
    tail_events = @($tail)
} | ConvertTo-Json -Depth 8

param(
    [string]$BaseToken = "XtSIbjGLSarQHDs3y2ncaWffnze",

    [string]$TableId = "tbl6u4j3HRjz9Ggk",

    [Parameter(Mandatory = $true)]
    [string]$RecordId,

    [Parameter(Mandatory = $true)]
    [string]$SessionType,

    [Parameter(Mandatory = $true)]
    [string]$SessionSource,

    [Parameter(Mandatory = $true)]
    [string]$WindowLog,

    [string]$PendingItems = "",

    [ValidateSet("user", "bot")]
    [string]$As = "bot",

    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$TableContract = [ordered]@{
    line = "B"
    table_name = "01_session"
    base_token_default = "XtSIbjGLSarQHDs3y2ncaWffnze"
    table_id_default = "tbl6u4j3HRjz9Ggk"
    note = "Default points to the local first-version B-line 01_session table. Override BaseToken/TableId for other users or workspaces."
}

$FieldMap = [ordered]@{
    session_type = "fld19k0EHl"
    session_source = "fldihzgeGW"
    window_log = "fldoGobDEz"
    pending_items = "fldS3vVzep"
}

$payload = [ordered]@{
    session_type = $SessionType
    session_source = $SessionSource
    window_log = $WindowLog
    pending_items = $PendingItems
}

$json = $payload | ConvertTo-Json -Compress -Depth 4
$tmpDirName = ".lark-tmp"
$tmpDir = Join-Path (Get-Location).Path $tmpDirName
$jsonFileName = "$([System.Guid]::NewGuid().ToString('N')).json"
$jsonFile = Join-Path $tmpDir $jsonFileName
$jsonFileArg = "@$tmpDirName/$jsonFileName"

try {
    if (-not (Test-Path -LiteralPath $tmpDir)) {
        New-Item -ItemType Directory -Path $tmpDir -Force | Out-Null
    }
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($jsonFile, $json, $utf8NoBom)

    $argsList = @(
        "base", "+record-upsert",
        "--base-token", $BaseToken,
        "--table-id", $TableId,
        "--record-id", $RecordId,
        "--json", $jsonFileArg,
        "--as", $As
    )

    if ($DryRun) {
        $argsList += "--dry-run"
    }

    & lark-cli @argsList
}
finally {
    if (Test-Path -LiteralPath $jsonFile) {
        Remove-Item -LiteralPath $jsonFile -Force -ErrorAction SilentlyContinue
    }
    if (Test-Path -LiteralPath $tmpDir) {
        $remaining = @(Get-ChildItem -LiteralPath $tmpDir -Force -ErrorAction SilentlyContinue)
        if ($remaining.Count -eq 0) {
            Remove-Item -LiteralPath $tmpDir -Force -ErrorAction SilentlyContinue
        }
    }
}

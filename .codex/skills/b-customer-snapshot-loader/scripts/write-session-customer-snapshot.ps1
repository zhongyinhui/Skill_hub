param(
    [string]$SessionBaseToken = "XtSIbjGLSarQHDs3y2ncaWffnze",

    [string]$SessionTableId = "tbl6u4j3HRjz9Ggk",

    [Parameter(Mandatory = $true)]
    [string]$RecordId,

    [string]$CustomerId = "",

    [string]$CustomerNameSnapshot = "",

    [string]$StartSnapshotRef = "",

    [string]$PendingItems = "",

    [ValidateSet("user", "bot")]
    [string]$As = "bot",

    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$SessionTableContract = [ordered]@{
    line = "B"
    table_name = "01_session"
    base_token_default = "XtSIbjGLSarQHDs3y2ncaWffnze"
    table_id_default = "tbl6u4j3HRjz9Ggk"
}

$SessionFieldMap = [ordered]@{
    customer_id = "fld0kKgYzg"
    customer_name_snapshot = "fldGp1MXFd"
    start_snapshot_ref = "fldFU71zf6"
    pending_items = "fldS3vVzep"
}

$payload = [ordered]@{}
if ($CustomerId -ne "") {
    $payload.customer_id = $CustomerId
}
if ($CustomerNameSnapshot -ne "") {
    $payload.customer_name_snapshot = $CustomerNameSnapshot
}
if ($StartSnapshotRef -ne "") {
    $payload.start_snapshot_ref = $StartSnapshotRef
}
$payload.pending_items = $PendingItems

if ($payload.Count -eq 1 -and $PendingItems -eq "") {
    throw "Nothing to write. Provide confirmed customer fields or PendingItems."
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
        "--base-token", $SessionBaseToken,
        "--table-id", $SessionTableId,
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

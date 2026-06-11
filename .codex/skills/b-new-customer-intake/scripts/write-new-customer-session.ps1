param(
    [string]$SessionBaseToken = "XtSIbjGLSarQHDs3y2ncaWffnze",

    [string]$SessionTableId = "tbl6u4j3HRjz9Ggk",

    [Parameter(Mandatory = $true)]
    [string]$RecordId,

    [Parameter(Mandatory = $true)]
    [string]$SessionType,

    [Parameter(Mandatory = $true)]
    [string]$CustomerNameSnapshot,

    [Parameter(Mandatory = $true)]
    [string]$RawInputRefs,

    [string]$PendingItems = "",

    [string]$WindowLog = "",

    [string]$AiAnalysisSummary = "",

    [ValidateSet("need_confirm", "active", "ready_for_blacklight", "closed")]
    [string]$SessionStatus = "need_confirm",

    [bool]$ReadyForBlacklight = $false,

    [ValidateSet("user", "bot")]
    [string]$As = "bot",

    [switch]$UseFieldIds,

    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

if ([string]::IsNullOrWhiteSpace($CustomerNameSnapshot)) {
    throw "CustomerNameSnapshot is required."
}
if ([string]::IsNullOrWhiteSpace($RawInputRefs)) {
    throw "RawInputRefs is required and must be traceable."
}

$SessionTableContract = [ordered]@{
    line = "B"
    table_name = "01_session"
    base_token_default = "XtSIbjGLSarQHDs3y2ncaWffnze"
    table_id_default = "tbl6u4j3HRjz9Ggk"
}

$SessionFieldMap = [ordered]@{
    session_type = "fld19k0EHl"
    customer_name_snapshot = "fldGp1MXFd"
    raw_input_refs = "fld6oO3sIZ"
    pending_items = "fldS3vVzep"
    window_log = "fldoGobDEz"
    ai_analysis_summary = "fldNXsP73x"
    session_status = "fldTa42TPL"
    ready_for_blacklight = "fldlf734Ar"
}

function Add-FieldValue {
    param(
        [System.Collections.IDictionary]$Payload,
        [string]$FieldName,
        [object]$Value
    )

    $key = $FieldName
    if ($UseFieldIds) {
        $key = $SessionFieldMap[$FieldName]
    }
    $Payload[$key] = $Value
}

$payload = [ordered]@{}
Add-FieldValue -Payload $payload -FieldName "session_type" -Value $SessionType
Add-FieldValue -Payload $payload -FieldName "customer_name_snapshot" -Value $CustomerNameSnapshot
Add-FieldValue -Payload $payload -FieldName "raw_input_refs" -Value $RawInputRefs
Add-FieldValue -Payload $payload -FieldName "pending_items" -Value $PendingItems
Add-FieldValue -Payload $payload -FieldName "session_status" -Value $SessionStatus
Add-FieldValue -Payload $payload -FieldName "ready_for_blacklight" -Value $ReadyForBlacklight

if ($WindowLog -ne "") {
    Add-FieldValue -Payload $payload -FieldName "window_log" -Value $WindowLog
}
if ($AiAnalysisSummary -ne "") {
    Add-FieldValue -Payload $payload -FieldName "ai_analysis_summary" -Value $AiAnalysisSummary
}

$json = $payload | ConvertTo-Json -Compress -Depth 8
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

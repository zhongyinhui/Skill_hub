param(
    [string]$BaseToken = "XtSIbjGLSarQHDs3y2ncaWffnze",

    [string]$TableId = "tbl6u4j3HRjz9Ggk",

    [Parameter(Mandatory = $true)]
    [string]$CodexSourceRef,

    [int]$Limit = 20,

    [ValidateSet("user", "bot")]
    [string]$As = "bot",

    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

if ([string]::IsNullOrWhiteSpace($CodexSourceRef)) {
    throw "CodexSourceRef is required."
}
if ($Limit -lt 1 -or $Limit -gt 200) {
    throw "Limit must be between 1 and 200."
}

$TableContract = [ordered]@{
    line = "B"
    table_name = "01_session"
    base_token_default = "XtSIbjGLSarQHDs3y2ncaWffnze"
    table_id_default = "tbl6u4j3HRjz9Ggk"
}

$FieldMap = [ordered]@{
    session_id = "fld9l16mCy"
    sales_id = "fldkHtOef5"
    sales_name = "fldqjP1krI"
    work_date = "fldriKhGrE"
    customer_id = "fld0kKgYzg"
    customer_name_snapshot = "fldGp1MXFd"
    session_type = "fld19k0EHl"
    session_source = "fldihzgeGW"
    session_status = "fldTa42TPL"
    start_time = "fldt792tJD"
    created_at = "fldf1cIedD"
    raw_input_refs = "fld6oO3sIZ"
    window_log = "fldoGobDEz"
    remark = "fldrEib3Wt"
}

$payload = [ordered]@{
    keyword = $CodexSourceRef
    search_fields = @("session_id", "raw_input_refs", "remark")
    select_fields = @("session_id", "sales_id", "sales_name", "work_date", "customer_id", "customer_name_snapshot", "session_type", "session_source", "session_status", "start_time", "created_at", "raw_input_refs", "window_log", "remark")
    limit = $Limit
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
        "base", "+record-search",
        "--base-token", $BaseToken,
        "--table-id", $TableId,
        "--json", $jsonFileArg,
        "--format", "json",
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

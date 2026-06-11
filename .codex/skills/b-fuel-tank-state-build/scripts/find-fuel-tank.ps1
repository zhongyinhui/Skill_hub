param(
    [string]$FuelTankBaseToken = "Ba0DbuHxaaonj2sxT4tcEwWonZf",

    [string]$FuelTankTableId = "tbloO6EEgyXFrwFG",

    [string]$SessionId = "",

    [string]$FuelTankId = "",

    [int]$Limit = 20,

    [ValidateSet("user", "bot")]
    [string]$As = "bot",

    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

if ([string]::IsNullOrWhiteSpace($SessionId) -and [string]::IsNullOrWhiteSpace($FuelTankId)) {
    throw "Provide SessionId or FuelTankId."
}
if ($Limit -lt 1 -or $Limit -gt 200) {
    throw "Limit must be between 1 and 200."
}

$keyword = $SessionId
if (-not [string]::IsNullOrWhiteSpace($FuelTankId)) {
    $keyword = $FuelTankId
}

$TableContract = [ordered]@{
    line = "B"
    table_name = "02_fuel_tank"
    base_token_default = "Ba0DbuHxaaonj2sxT4tcEwWonZf"
    table_id_default = "tbloO6EEgyXFrwFG"
}

$FieldMap = [ordered]@{
    fuel_tank_id = "fldP3TwKXy"
    session_id = "fld79G5XL4"
    customer_id = "fld1HVBbuz"
    sales_id = "fldiRPQEzA"
    work_date = "fldifwfyTK"
    start_snapshot_ref = "fldo6WNlQY"
    new_inputs_today = "fldFwqPeqq"
    status = "fldTaPxssT"
    updated_at = "fldGlRTEUC"
}

$payload = [ordered]@{
    keyword = $keyword
    search_fields = @("fuel_tank_id", "session_id")
    select_fields = @("fuel_tank_id", "session_id", "customer_id", "sales_id", "work_date", "start_snapshot_ref", "new_inputs_today", "status", "updated_at")
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
        "--base-token", $FuelTankBaseToken,
        "--table-id", $FuelTankTableId,
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

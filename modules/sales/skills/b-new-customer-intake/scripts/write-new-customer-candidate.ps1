param(
    [string]$BlacklightBaseToken = "QznJbdaDKaM8O0s2GFqcMkjsncc",

    [string]$BlacklightTableId = "tbldZtvYSwT5C8KB",

    [string]$RecordId = "",

    [Parameter(Mandatory = $true)]
    [string]$BlacklightOutputId,

    [ValidateSet("a_ready_package", "orphan_confirm")]
    [string]$OutputType = "a_ready_package",

    [string[]]$TargetLine = @("A"),

    [string]$ConfirmStatus = "need_confirm",

    [bool]$HumanConfirmRequired = $true,

    [string]$OrphanItems = "",

    [string]$AReadyPackage = "",

    [string]$AReadyPackageFile = "",

    [Parameter(Mandatory = $true)]
    [string]$SourceSessionIds,

    [Parameter(Mandatory = $true)]
    [string]$SourceRawInputRefs,

    [string]$SalesId = "",

    [string]$CustomerId = "",

    [Parameter(Mandatory = $true)]
    [string]$WorkDate,

    [string]$CreatedBy = "b-new-customer-intake",

    [string]$TargetStatus = "pending_a_confirm",

    [string]$Remark = "",

    [string]$EffectiveEventsSummary = "",

    [ValidateSet("user", "bot")]
    [string]$As = "bot",

    [switch]$UseFieldIds,

    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

if ([string]::IsNullOrWhiteSpace($BlacklightOutputId)) {
    throw "BlacklightOutputId is required."
}
if ([string]::IsNullOrWhiteSpace($AReadyPackage) -and [string]::IsNullOrWhiteSpace($AReadyPackageFile)) {
    throw "AReadyPackage or AReadyPackageFile is required."
}
if ($AReadyPackageFile -ne "") {
    if (-not (Test-Path -LiteralPath $AReadyPackageFile)) {
        throw "AReadyPackageFile does not exist: $AReadyPackageFile"
    }
    $resolvedPackageFile = (Resolve-Path -LiteralPath $AReadyPackageFile).Path
    $AReadyPackage = [System.IO.File]::ReadAllText($resolvedPackageFile, [System.Text.Encoding]::UTF8)
}
if ([string]::IsNullOrWhiteSpace($SourceSessionIds)) {
    throw "SourceSessionIds is required."
}
if ([string]::IsNullOrWhiteSpace($SourceRawInputRefs)) {
    throw "SourceRawInputRefs is required and must be traceable."
}
if ([string]::IsNullOrWhiteSpace($WorkDate)) {
    throw "WorkDate is required. Use an absolute date such as 2026-06-08."
}

$BlacklightTableContract = [ordered]@{
    line = "B"
    table_name = "03_blacklight_output"
    base_token_default = "QznJbdaDKaM8O0s2GFqcMkjsncc"
    table_id_default = "tbldZtvYSwT5C8KB"
}

$BlacklightFieldMap = [ordered]@{
    blacklight_output_id = "fldDK5Aegp"
    output_type = "fldyiXR2fZ"
    target_line = "fldHxSt8oS"
    confirm_status = "fldwXd47fE"
    human_confirm_required = "fldcgq6nGr"
    orphan_items = "fldr5wl4Ks"
    a_ready_package = "fld7rNsZAl"
    source_session_ids = "fldmnNlJQR"
    source_raw_input_refs = "fldxY0v2EH"
    sales_id = "fldoOZmfAH"
    customer_id = "fldgWlq0wW"
    work_date = "fldGIh5vTZ"
    created_by = "fldZqijdD1"
    target_status = "fldgpjIyVq"
    remark = "fldmS6XsUy"
    effective_events_summary = "fldpT6zXPM"
}

function Add-FieldValue {
    param(
        [System.Collections.IDictionary]$Payload,
        [string]$FieldName,
        [object]$Value
    )

    $key = $FieldName
    if ($UseFieldIds) {
        $key = $BlacklightFieldMap[$FieldName]
    }
    $Payload[$key] = $Value
}

$payload = [ordered]@{}
Add-FieldValue -Payload $payload -FieldName "blacklight_output_id" -Value $BlacklightOutputId
Add-FieldValue -Payload $payload -FieldName "output_type" -Value $OutputType
Add-FieldValue -Payload $payload -FieldName "target_line" -Value $TargetLine
Add-FieldValue -Payload $payload -FieldName "confirm_status" -Value $ConfirmStatus
Add-FieldValue -Payload $payload -FieldName "human_confirm_required" -Value $HumanConfirmRequired
Add-FieldValue -Payload $payload -FieldName "a_ready_package" -Value $AReadyPackage
Add-FieldValue -Payload $payload -FieldName "source_session_ids" -Value $SourceSessionIds
Add-FieldValue -Payload $payload -FieldName "source_raw_input_refs" -Value $SourceRawInputRefs
Add-FieldValue -Payload $payload -FieldName "work_date" -Value $WorkDate
Add-FieldValue -Payload $payload -FieldName "created_by" -Value $CreatedBy
Add-FieldValue -Payload $payload -FieldName "target_status" -Value $TargetStatus

if ($OrphanItems -ne "") {
    Add-FieldValue -Payload $payload -FieldName "orphan_items" -Value $OrphanItems
}
if ($SalesId -ne "") {
    Add-FieldValue -Payload $payload -FieldName "sales_id" -Value $SalesId
}
if ($CustomerId -ne "") {
    Add-FieldValue -Payload $payload -FieldName "customer_id" -Value $CustomerId
}
if ($Remark -ne "") {
    Add-FieldValue -Payload $payload -FieldName "remark" -Value $Remark
}
if ($EffectiveEventsSummary -ne "") {
    Add-FieldValue -Payload $payload -FieldName "effective_events_summary" -Value $EffectiveEventsSummary
}

$json = $payload | ConvertTo-Json -Compress -Depth 10
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
        "--base-token", $BlacklightBaseToken,
        "--table-id", $BlacklightTableId,
        "--json", $jsonFileArg,
        "--as", $As
    )
    if ($RecordId -ne "") {
        $argsList += @("--record-id", $RecordId)
    }
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

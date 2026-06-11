param(
    [string]$BaseToken = "XtSIbjGLSarQHDs3y2ncaWffnze",

    [string]$TableId = "tbl6u4j3HRjz9Ggk",

    [string]$RecordId = "",

    [Parameter(Mandatory = $true)]
    [string]$SessionId,

    [Parameter(Mandatory = $true)]
    [string]$SalesId,

    [Parameter(Mandatory = $true)]
    [string]$SalesName,

    [Parameter(Mandatory = $true)]
    [string]$WorkDate,

    [Parameter(Mandatory = $true)]
    [string]$CodexSourceRef,

    [string]$CustomerId = "",

    [string]$CustomerNameSnapshot = "",

    [Parameter(Mandatory = $true)]
    [string]$SessionType,

    [Parameter(Mandatory = $true)]
    [string]$SessionSource,

    [string]$SessionStatus = "running",

    [Parameter(Mandatory = $true)]
    [string]$StartTime,

    [Parameter(Mandatory = $true)]
    [string]$CreatedAt,

    [string]$WindowLog = "",

    [string]$Remark = "",

    [ValidateSet("feishu_self", "manual_confirmed", "external_runtime", "unknown")]
    [string]$OperatorIdentitySource = "unknown",

    [string]$OperatorIdentityRef = "",

    [ValidateSet("user", "bot")]
    [string]$As = "bot",

    [switch]$UseFieldIds,

    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

if ([string]::IsNullOrWhiteSpace($SessionId)) {
    throw "SessionId is required."
}
if ([string]::IsNullOrWhiteSpace($SalesId)) {
    throw "SalesId is required."
}
if ([string]::IsNullOrWhiteSpace($SalesName)) {
    throw "SalesName is required."
}
if ($WorkDate -notmatch '^\d{4}-\d{2}-\d{2}$') {
    throw "WorkDate must be yyyy-MM-dd."
}
if ([string]::IsNullOrWhiteSpace($CodexSourceRef)) {
    throw "CodexSourceRef is required."
}
if ($OperatorIdentitySource -eq "unknown" -and $SessionStatus -ne "need_confirm") {
    throw "Unknown operator identity can only be registered with SessionStatus need_confirm."
}
if ($OperatorIdentitySource -ne "unknown" -and [string]::IsNullOrWhiteSpace($OperatorIdentityRef)) {
    throw "OperatorIdentityRef is required when OperatorIdentitySource is verified."
}
if ([string]::IsNullOrWhiteSpace($SessionType)) {
    throw "SessionType is required."
}
if ([string]::IsNullOrWhiteSpace($SessionSource)) {
    throw "SessionSource is required."
}
if ($StartTime -notmatch '^\d{4}-\d{2}-\d{2} \d{2}:\d{2}(:\d{2})?$') {
    throw "StartTime must be yyyy-MM-dd HH:mm or yyyy-MM-dd HH:mm:ss."
}
if ($CreatedAt -notmatch '^\d{4}-\d{2}-\d{2} \d{2}:\d{2}(:\d{2})?$') {
    throw "CreatedAt must be yyyy-MM-dd HH:mm or yyyy-MM-dd HH:mm:ss."
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

function Add-FieldValue {
    param(
        [System.Collections.IDictionary]$Payload,
        [string]$FieldName,
        [object]$Value
    )

    $key = $FieldName
    if ($UseFieldIds) {
        $key = $FieldMap[$FieldName]
    }
    $Payload[$key] = $Value
}

$payload = [ordered]@{}
Add-FieldValue -Payload $payload -FieldName "session_id" -Value $SessionId
Add-FieldValue -Payload $payload -FieldName "sales_id" -Value $SalesId
Add-FieldValue -Payload $payload -FieldName "sales_name" -Value $SalesName
Add-FieldValue -Payload $payload -FieldName "work_date" -Value $WorkDate
Add-FieldValue -Payload $payload -FieldName "session_type" -Value $SessionType
Add-FieldValue -Payload $payload -FieldName "session_source" -Value $SessionSource
Add-FieldValue -Payload $payload -FieldName "session_status" -Value $SessionStatus
Add-FieldValue -Payload $payload -FieldName "start_time" -Value $StartTime
Add-FieldValue -Payload $payload -FieldName "created_at" -Value $CreatedAt
Add-FieldValue -Payload $payload -FieldName "raw_input_refs" -Value $CodexSourceRef

if ($CustomerId -ne "") {
    Add-FieldValue -Payload $payload -FieldName "customer_id" -Value $CustomerId
}
if ($CustomerNameSnapshot -ne "") {
    Add-FieldValue -Payload $payload -FieldName "customer_name_snapshot" -Value $CustomerNameSnapshot
}
if ($WindowLog -ne "") {
    Add-FieldValue -Payload $payload -FieldName "window_log" -Value $WindowLog
}
if ($Remark -ne "") {
    $Remark = "$Remark | identity_source=$OperatorIdentitySource; identity_ref=$OperatorIdentityRef"
    Add-FieldValue -Payload $payload -FieldName "remark" -Value $Remark
}
else {
    Add-FieldValue -Payload $payload -FieldName "remark" -Value "identity_source=$OperatorIdentitySource; identity_ref=$OperatorIdentityRef"
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
        "--base-token", $BaseToken,
        "--table-id", $TableId,
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

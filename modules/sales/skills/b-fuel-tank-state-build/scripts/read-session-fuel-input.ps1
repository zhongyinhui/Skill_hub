param(
    [string]$SessionBaseToken = "XtSIbjGLSarQHDs3y2ncaWffnze",

    [string]$SessionTableId = "tbl6u4j3HRjz9Ggk",

    [Parameter(Mandatory = $true)]
    [string]$RecordId,

    [ValidateSet("user", "bot")]
    [string]$As = "bot",

    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

if ([string]::IsNullOrWhiteSpace($RecordId)) {
    throw "RecordId is required."
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
    start_snapshot_ref = "fldFU71zf6"
    raw_input_refs = "fld6oO3sIZ"
    ai_analysis_summary = "fldNXsP73x"
    updated_at = "fldXP35X3X"
}

$argsList = @(
    "base", "+record-get",
    "--base-token", $SessionBaseToken,
    "--table-id", $SessionTableId,
    "--record-id", $RecordId,
    "--format", "json",
    "--as", $As
)

foreach ($fieldId in $FieldMap.Values) {
    $argsList += @("--field-id", $fieldId)
}

if ($DryRun) {
    $argsList += "--dry-run"
}

& lark-cli @argsList

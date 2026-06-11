param(
    [string]$BaseToken = "XtSIbjGLSarQHDs3y2ncaWffnze",

    [string]$TableId = "tbl6u4j3HRjz9Ggk",

    [int]$Limit = 20,

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
    session_id = "fld9l16mCy"
    sales_id = "fldkHtOef5"
    sales_name = "fldqjP1krI"
    work_date = "fldriKhGrE"
    session_type = "fld19k0EHl"
    session_source = "fldihzgeGW"
    session_status = "fldTa42TPL"
    customer_id = "fld0kKgYzg"
    window_log = "fldoGobDEz"
    pending_items = "fldS3vVzep"
}

if ($Limit -lt 1 -or $Limit -gt 200) {
    throw "Limit must be between 1 and 200."
}

$fields = @(
    "session_id",
    "sales_id",
    "sales_name",
    "work_date",
    "session_type",
    "session_source",
    "session_status",
    "customer_id",
    "window_log",
    "pending_items"
)

$argsList = @(
    "base", "+record-list",
    "--base-token", $BaseToken,
    "--table-id", $TableId,
    "--limit", "$Limit",
    "--format", "json",
    "--as", $As
)

if ($DryRun) {
    $argsList += "--dry-run"
}

foreach ($field in $fields) {
    $argsList += @("--field-id", $field)
}

& lark-cli @argsList

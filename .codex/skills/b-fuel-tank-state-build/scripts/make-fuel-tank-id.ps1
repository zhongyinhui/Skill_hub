param(
    [Parameter(Mandatory = $true)]
    [string]$SessionId,

    [Parameter(Mandatory = $true)]
    [string]$CustomerId,

    [Parameter(Mandatory = $true)]
    [string]$SalesId,

    [Parameter(Mandatory = $true)]
    [string]$WorkDate,

    [switch]$Raw
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

if ([string]::IsNullOrWhiteSpace($SessionId)) {
    throw "SessionId is required."
}
if ([string]::IsNullOrWhiteSpace($CustomerId)) {
    throw "CustomerId is required. Run B-SK02 or B-SK03 before building FuelTank."
}
if ([string]::IsNullOrWhiteSpace($SalesId)) {
    throw "SalesId is required."
}
if ($WorkDate -notmatch '^\d{4}-\d{2}-\d{2}$') {
    throw "WorkDate must be yyyy-MM-dd."
}

$seed = "b-fuel-tank-state-build.v1|session_id=$SessionId|customer_id=$CustomerId|sales_id=$SalesId|work_date=$WorkDate"
$bytes = [System.Text.Encoding]::UTF8.GetBytes($seed.ToLowerInvariant())
$sha = [System.Security.Cryptography.SHA256]::Create()
$hash = [BitConverter]::ToString($sha.ComputeHash($bytes)).Replace("-", "").Substring(0, 12).ToUpperInvariant()
$datePart = $WorkDate.Replace("-", "")
$fuelTankId = "BFTK-$datePart-$hash"

if ($Raw) {
    $fuelTankId
    return
}

[ordered]@{
    schema = "b.fuel_tank_id.v1"
    fuel_tank_id = $fuelTankId
    session_id = $SessionId
    customer_id = $CustomerId
    sales_id = $SalesId
    work_date = $WorkDate
    seed_sha256_prefix = $hash
    stable_rule = "session_id+customer_id+sales_id+work_date"
} | ConvertTo-Json -Depth 6

param(
    [string]$BindingFile = "",

    [switch]$RetireActive,

    [Parameter(Mandatory = $true)]
    [string]$SalesId,

    [Parameter(Mandatory = $true)]
    [string]$SalesName,

    [ValidateSet("feishu_self", "manual_confirmed", "external_runtime")]
    [string]$IdentitySource = "manual_confirmed",

    [Parameter(Mandatory = $true)]
    [string]$IdentityRef,

    [Parameter(Mandatory = $true)]
    [string]$BLineKnowledgeBaseKey,

    [Parameter(Mandatory = $true)]
    [string]$SessionBaseToken,

    [Parameter(Mandatory = $true)]
    [string]$SessionTableId,

    [Parameter(Mandatory = $true)]
    [string]$ActiveFrom,

    [string]$ActiveTo = "",

    [string]$HandoverReason = "normal",

    [string]$ConfirmedBy = "",

    [string]$ConfirmedAt = "",

    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

if ([string]::IsNullOrWhiteSpace($BindingFile)) {
    if (-not [string]::IsNullOrWhiteSpace($env:BLINE_STORAGE_BINDING_FILE)) {
        $BindingFile = $env:BLINE_STORAGE_BINDING_FILE
    }
    else {
        $BindingFile = Join-Path $env:USERPROFILE ".codex-bline\storage-bindings.json"
    }
}

try {
    $activeFromDate = [datetime]::Parse($ActiveFrom)
}
catch {
    throw "ActiveFrom must be an absolute datetime, such as 2026-06-08 00:00:00."
}
if ($ActiveTo -ne "") {
    try {
        [void][datetime]::Parse($ActiveTo)
    }
    catch {
        throw "ActiveTo must be an absolute datetime when provided."
    }
}
if ([string]::IsNullOrWhiteSpace($ConfirmedAt)) {
    $ConfirmedAt = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
}

$config = [ordered]@{
    schema_version = "1.0"
    bindings = @()
}

if (Test-Path -LiteralPath $BindingFile) {
    $raw = [System.IO.File]::ReadAllText((Resolve-Path -LiteralPath $BindingFile).Path, [System.Text.Encoding]::UTF8)
    if (-not [string]::IsNullOrWhiteSpace($raw)) {
        $existing = $raw | ConvertFrom-Json
        $config.schema_version = [string]$existing.schema_version
        $config.bindings = @($existing.bindings)
    }
}

$newBindings = @()
foreach ($binding in @($config.bindings)) {
    if ($RetireActive -and [string]$binding.status -eq "active" -and [string]::IsNullOrWhiteSpace([string]$binding.active_to)) {
        $binding.status = "retired"
        $binding.active_to = $activeFromDate.ToString("yyyy-MM-dd HH:mm:ss")
    }
    $newBindings += $binding
}

$basis = "$SalesId|$BLineKnowledgeBaseKey|$SessionBaseToken|$SessionTableId|$($activeFromDate.ToString('yyyy-MM-dd HH:mm:ss'))"
$sha = [System.Security.Cryptography.SHA256]::Create()
try {
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($basis)
    $hashBytes = $sha.ComputeHash($bytes)
    $hash = -join ($hashBytes | ForEach-Object { $_.ToString("x2") })
}
finally {
    $sha.Dispose()
}

$bindingId = "bind-$($activeFromDate.ToString('yyyyMMddHHmmss'))-$($hash.Substring(0, 8))"
$newBinding = [ordered]@{
    binding_id = $bindingId
    status = "active"
    active_from = $activeFromDate.ToString("yyyy-MM-dd HH:mm:ss")
    active_to = $ActiveTo
    sales_id = $SalesId
    sales_name = $SalesName
    identity_source = $IdentitySource
    identity_ref = $IdentityRef
    bline_knowledge_base_key = $BLineKnowledgeBaseKey
    session_base_token = $SessionBaseToken
    session_table_id = $SessionTableId
    handover_reason = $HandoverReason
    confirmed_by = $ConfirmedBy
    confirmed_at = $ConfirmedAt
}
$newBindings += $newBinding

$output = [ordered]@{
    schema_version = "1.0"
    bindings = $newBindings
}

if ($DryRun) {
    [ordered]@{
        dry_run = $true
        binding_file = $BindingFile
        new_binding = $newBinding
        resulting_config = $output
    } | ConvertTo-Json -Depth 10
    return
}

$dir = Split-Path -Parent $BindingFile
if (-not (Test-Path -LiteralPath $dir)) {
    New-Item -ItemType Directory -Path $dir -Force | Out-Null
}
$json = $output | ConvertTo-Json -Depth 10
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($BindingFile, $json, $utf8NoBom)

[ordered]@{
    written = $true
    binding_file = (Resolve-Path -LiteralPath $BindingFile).Path
    new_binding_id = $bindingId
    retired_active = [bool]$RetireActive
} | ConvertTo-Json -Depth 6

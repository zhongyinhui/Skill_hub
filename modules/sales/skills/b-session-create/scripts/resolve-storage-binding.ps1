param(
    [string]$BindingFile = "",

    [Parameter(Mandatory = $true)]
    [string]$AtTime,

    [switch]$RequireActive
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

if (-not (Test-Path -LiteralPath $BindingFile)) {
    [ordered]@{
        binding_resolved = $false
        status = "missing_binding_file"
        binding_file = $BindingFile
        required_session_status = "need_confirm"
        reason = "No local storage binding file. Codex sessions cannot be assigned to a salesperson/table safely."
    } | ConvertTo-Json -Depth 6
    return
}

try {
    $targetTime = [datetime]::Parse($AtTime)
}
catch {
    throw "AtTime must be an absolute datetime, such as 2026-06-08 11:50:00."
}

$raw = [System.IO.File]::ReadAllText((Resolve-Path -LiteralPath $BindingFile).Path, [System.Text.Encoding]::UTF8)
$config = $raw | ConvertFrom-Json
$bindings = @($config.bindings)

$matches = @()
foreach ($binding in $bindings) {
    $status = [string]$binding.status
    if ($RequireActive -and $status -ne "active") {
        continue
    }

    $fromOk = $true
    $toOk = $true
    if (-not [string]::IsNullOrWhiteSpace([string]$binding.active_from)) {
        $fromOk = $targetTime -ge [datetime]::Parse([string]$binding.active_from)
    }
    if (-not [string]::IsNullOrWhiteSpace([string]$binding.active_to)) {
        $toOk = $targetTime -lt [datetime]::Parse([string]$binding.active_to)
    }

    if ($fromOk -and $toOk) {
        $matches += $binding
    }
}

if ($matches.Count -eq 0) {
    [ordered]@{
        binding_resolved = $false
        status = "no_matching_binding"
        binding_file = (Resolve-Path -LiteralPath $BindingFile).Path
        at_time = $targetTime.ToString("yyyy-MM-dd HH:mm:ss")
        required_session_status = "need_confirm"
        reason = "No binding covers this Codex session time."
    } | ConvertTo-Json -Depth 6
    return
}

if ($matches.Count -gt 1) {
    [ordered]@{
        binding_resolved = $false
        status = "ambiguous_binding"
        binding_file = (Resolve-Path -LiteralPath $BindingFile).Path
        at_time = $targetTime.ToString("yyyy-MM-dd HH:mm:ss")
        matched_binding_ids = @($matches | ForEach-Object { [string]$_.binding_id })
        required_session_status = "need_confirm"
        reason = "Multiple bindings cover this Codex session time."
    } | ConvertTo-Json -Depth 6
    return
}

$match = $matches[0]
[ordered]@{
    binding_resolved = $true
    status = "resolved"
    binding_file = (Resolve-Path -LiteralPath $BindingFile).Path
    at_time = $targetTime.ToString("yyyy-MM-dd HH:mm:ss")
    binding_id = [string]$match.binding_id
    binding_status = [string]$match.status
    active_from = [string]$match.active_from
    active_to = [string]$match.active_to
    sales_id = [string]$match.sales_id
    sales_name = [string]$match.sales_name
    identity_source = [string]$match.identity_source
    identity_ref = [string]$match.identity_ref
    bline_knowledge_base_key = [string]$match.bline_knowledge_base_key
    session_base_token = [string]$match.session_base_token
    session_table_id = [string]$match.session_table_id
    handover_reason = [string]$match.handover_reason
} | ConvertTo-Json -Depth 6

param(
    [string]$BindingFile = "",

    [Parameter(Mandatory = $true)]
    [string]$AtTime,

    [switch]$RequireActive
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$resolveScript = Join-Path $PSScriptRoot "resolve-storage-binding.ps1"
if (-not (Test-Path -LiteralPath $resolveScript)) {
    throw "resolve-storage-binding.ps1 not found next to ensure-storage-binding.ps1."
}

$argsList = @("-AtTime", $AtTime)
if ($BindingFile -ne "") {
    $argsList += @("-BindingFile", $BindingFile)
}
if ($RequireActive) {
    $argsList += "-RequireActive"
}

$raw = & powershell -ExecutionPolicy Bypass -File $resolveScript @argsList
$resolved = ($raw | Out-String) | ConvertFrom-Json

if ($resolved.binding_resolved -eq $true) {
    [ordered]@{
        binding_gate = "continue"
        reason = "A unique storage binding covers this Codex session time."
        binding = $resolved
        next_step = "register_codex_session"
    } | ConvertTo-Json -Depth 10
    return
}

$questionFields = @(
    [ordered]@{
        id = "sales_id"
        question = "Which sales_id owns this Codex sessions directory now?"
        required = $true
    },
    [ordered]@{
        id = "sales_name"
        question = "What is the sales_name?"
        required = $true
    },
    [ordered]@{
        id = "identity_source"
        question = "What is the identity_source: feishu_self, manual_confirmed, or external_runtime?"
        required = $true
    },
    [ordered]@{
        id = "identity_ref"
        question = "What is the identity_ref, such as Feishu open_id, manager confirmation, or handover ticket?"
        required = $true
    },
    [ordered]@{
        id = "session_base_token"
        question = "What is the B-line session Base token for this salesperson?"
        required = $true
    },
    [ordered]@{
        id = "session_table_id"
        question = "What is the B-line 01_session table id for this salesperson?"
        required = $true
    },
    [ordered]@{
        id = "active_from"
        question = "When does this binding start? Use yyyy-MM-dd HH:mm:ss."
        required = $true
    },
    [ordered]@{
        id = "cutover_at"
        question = "If this is handover or account reuse, what is the exact cutover_at? Use yyyy-MM-dd HH:mm:ss."
        required = $false
    },
    [ordered]@{
        id = "old_sales_id"
        question = "If this is handover or account reuse, which old_sales_id owned sessions before cutover_at?"
        required = $false
    },
    [ordered]@{
        id = "new_sales_id"
        question = "If this is handover or account reuse, which new_sales_id owns sessions from cutover_at?"
        required = $false
    },
    [ordered]@{
        id = "handover_proof_ref"
        question = "What proof confirms the handover, such as ticket id, manager confirmation, Feishu open_id, or SSO record?"
        required = $false
    },
    [ordered]@{
        id = "handover_reason"
        question = "Is this normal, employee_leave, account_reuse, or device_reassignment?"
        required = $true
    },
    [ordered]@{
        id = "retire_active"
        question = "If this is reassignment or account reuse, should the active old binding be retired first?"
        required = $false
    }
)

[ordered]@{
    binding_gate = "ask_user"
    status = [string]$resolved.status
    reason = [string]$resolved.reason
    at_time = $AtTime
    binding_file = [string]$resolved.binding_file
    required_session_status = "need_confirm"
    prompt = "No safe Codex sessions to salesperson/table binding found. Collect binding fields first, then run write-local-storage-binding.ps1."
    question_fields = $questionFields
    next_step = "collect_binding_then_write_local_storage_binding"
} | ConvertTo-Json -Depth 10

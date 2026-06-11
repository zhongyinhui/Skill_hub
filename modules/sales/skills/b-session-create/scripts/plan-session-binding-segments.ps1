param(
    [Parameter(Mandatory = $true)]
    [string]$SessionPath,

    [string]$BindingFile = "",

    [switch]$RequireActive
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

if (-not (Test-Path -LiteralPath $SessionPath)) {
    throw "SessionPath does not exist: $SessionPath"
}

if ([string]::IsNullOrWhiteSpace($BindingFile)) {
    if (-not [string]::IsNullOrWhiteSpace($env:BLINE_STORAGE_BINDING_FILE)) {
        $BindingFile = $env:BLINE_STORAGE_BINDING_FILE
    }
    else {
        $BindingFile = Join-Path $env:USERPROFILE ".codex-bline\storage-bindings.json"
    }
}

function Convert-ToLocalComparableTime {
    param([string]$Value)

    if ([string]::IsNullOrWhiteSpace($Value)) {
        return $null
    }

    try {
        return ([datetimeoffset]::Parse($Value)).LocalDateTime
    }
    catch {
        return ([datetime]::Parse($Value))
    }
}

function Get-BindingMatches {
    param(
        [datetime]$AtTime,
        [array]$Bindings,
        [bool]$ActiveOnly
    )

    $matches = @()
    foreach ($binding in $Bindings) {
        $status = [string]$binding.status
        if ($ActiveOnly -and $status -ne "active") {
            continue
        }

        $fromOk = $true
        $toOk = $true
        if (-not [string]::IsNullOrWhiteSpace([string]$binding.active_from)) {
            $fromOk = $AtTime -ge (Convert-ToLocalComparableTime -Value ([string]$binding.active_from))
        }
        if (-not [string]::IsNullOrWhiteSpace([string]$binding.active_to)) {
            $toOk = $AtTime -lt (Convert-ToLocalComparableTime -Value ([string]$binding.active_to))
        }

        if ($fromOk -and $toOk) {
            $matches += $binding
        }
    }
    return $matches
}

function Get-SegmentKey {
    param(
        [string]$Status,
        [object]$Binding
    )

    if ($Status -eq "resolved" -and $null -ne $Binding) {
        return "resolved|$([string]$Binding.binding_id)"
    }
    return $Status
}

function Get-HandoverQuestionFields {
    return @(
        [ordered]@{
            id = "cutover_at"
            question = "What is the exact handover cutover_at? Use yyyy-MM-dd HH:mm:ss."
            required = $true
        },
        [ordered]@{
            id = "old_sales_id"
            question = "Which old_sales_id owned Codex sessions before cutover_at?"
            required = $true
        },
        [ordered]@{
            id = "new_sales_id"
            question = "Which new_sales_id owns Codex sessions from cutover_at?"
            required = $true
        },
        [ordered]@{
            id = "identity_source"
            question = "What is the verified identity source: feishu_self, manual_confirmed, or external_runtime?"
            required = $true
        },
        [ordered]@{
            id = "handover_proof_ref"
            question = "What proof confirms this handover, such as ticket id, manager confirmation, Feishu open_id, or SSO record?"
            required = $true
        },
        [ordered]@{
            id = "session_base_token"
            question = "What is the B-line session Base token for the target salesperson?"
            required = $true
        },
        [ordered]@{
            id = "session_table_id"
            question = "What is the B-line 01_session table id for the target salesperson?"
            required = $true
        }
    )
}

function New-Segment {
    param(
        [string]$Status,
        [object]$Binding,
        [string]$SourceRef,
        [int]$LineNumber,
        [datetime]$EventTime
    )

    $bindingId = ""
    $salesId = ""
    $salesName = ""
    $kbKey = ""
    $baseToken = ""
    $tableId = ""
    $identitySource = ""
    $identityRef = ""

    if ($Status -eq "resolved" -and $null -ne $Binding) {
        $bindingId = [string]$Binding.binding_id
        $salesId = [string]$Binding.sales_id
        $salesName = [string]$Binding.sales_name
        $kbKey = [string]$Binding.bline_knowledge_base_key
        $baseToken = [string]$Binding.session_base_token
        $tableId = [string]$Binding.session_table_id
        $identitySource = [string]$Binding.identity_source
        $identityRef = [string]$Binding.identity_ref
    }

    $segmentSourceRef = $SourceRef
    if (-not [string]::IsNullOrWhiteSpace($bindingId)) {
        $segmentSourceRef = "$SourceRef#binding:$bindingId"
    }
    elseif ($Status -ne "resolved") {
        $segmentSourceRef = "$SourceRef#segment:$Status"
    }

    return [ordered]@{
        segment_status = $Status
        binding_id = $bindingId
        sales_id = $salesId
        sales_name = $salesName
        bline_knowledge_base_key = $kbKey
        session_base_token = $baseToken
        session_table_id = $tableId
        identity_source = $identitySource
        identity_ref = $identityRef
        codex_segment_ref = $segmentSourceRef
        first_line = $LineNumber
        last_line = $LineNumber
        first_event_timestamp = $EventTime.ToString("yyyy-MM-dd HH:mm:ss")
        last_event_timestamp = $EventTime.ToString("yyyy-MM-dd HH:mm:ss")
        event_count = 1
    }
}

if (-not (Test-Path -LiteralPath $BindingFile)) {
    [ordered]@{
        segment_plan_status = "need_confirm"
        reason = "No local storage binding file. Cannot safely assign Codex session events to old or new salesperson."
        binding_file = $BindingFile
        required_session_status = "need_confirm"
        question_fields = @(Get-HandoverQuestionFields)
        segments = @()
    } | ConvertTo-Json -Depth 10
    return
}

$resolvedSessionPath = (Resolve-Path -LiteralPath $SessionPath).Path
$resolvedBindingFile = (Resolve-Path -LiteralPath $BindingFile).Path
$bindingRaw = [System.IO.File]::ReadAllText($resolvedBindingFile, [System.Text.Encoding]::UTF8)
$bindingConfig = $bindingRaw | ConvertFrom-Json
$bindings = @($bindingConfig.bindings)

$segments = @()
$currentSegment = $null
$currentKey = ""
$lineCount = 0
$eventCount = 0
$parseErrors = 0
$timestamplessEvents = 0
$firstTimestamp = $null
$lastTimestamp = $null
$sessionMeta = $null

$stream = [System.IO.File]::Open($resolvedSessionPath, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
$reader = New-Object System.IO.StreamReader($stream, [System.Text.Encoding]::UTF8)
try {
    while (($line = $reader.ReadLine()) -ne $null) {
        $lineCount++
        if ([string]::IsNullOrWhiteSpace($line)) {
            continue
        }

        try {
            $obj = $line | ConvertFrom-Json
        }
        catch {
            $parseErrors++
            continue
        }

        if ($obj.type -eq "session_meta" -and $obj.payload) {
            $sessionMeta = $obj.payload
        }

        $eventTime = Convert-ToLocalComparableTime -Value ([string]$obj.timestamp)
        if ($null -eq $eventTime) {
            $timestamplessEvents++
            continue
        }

        $eventCount++
        if ($null -eq $firstTimestamp) {
            $firstTimestamp = $eventTime
        }
        $lastTimestamp = $eventTime

        $matches = @(Get-BindingMatches -AtTime $eventTime -Bindings $bindings -ActiveOnly ([bool]$RequireActive))
        $status = "resolved"
        $binding = $null
        if ($matches.Count -eq 0) {
            $status = "need_confirm"
        }
        elseif ($matches.Count -gt 1) {
            $status = "ambiguous_binding"
        }
        else {
            $binding = $matches[0]
        }

        $key = Get-SegmentKey -Status $status -Binding $binding
        if ($null -eq $currentSegment -or $key -ne $currentKey) {
            if ($null -ne $currentSegment) {
                $segments += $currentSegment
            }
            $sourceRefForNewSegment = ""
            $currentSegment = $null
            $currentKey = $key
            $sourceRefForNewSegment = "__SOURCE_REF_PLACEHOLDER__"
            $currentSegment = New-Segment -Status $status -Binding $binding -SourceRef $sourceRefForNewSegment -LineNumber $lineCount -EventTime $eventTime
        }
        else {
            $currentSegment.last_line = $lineCount
            $currentSegment.last_event_timestamp = $eventTime.ToString("yyyy-MM-dd HH:mm:ss")
            $currentSegment.event_count = [int]$currentSegment.event_count + 1
        }
    }
}
finally {
    $reader.Close()
    $stream.Close()
}

if ($null -ne $currentSegment) {
    $segments += $currentSegment
}

$codexSessionId = ""
if ($sessionMeta -and $sessionMeta.id) {
    $codexSessionId = [string]$sessionMeta.id
}

if ([string]::IsNullOrWhiteSpace($codexSessionId)) {
    $codexSourceRef = "local-codex-session-jsonl:$resolvedSessionPath"
}
else {
    $codexSourceRef = "codex-session:$codexSessionId"
}

foreach ($segment in $segments) {
    $segment.codex_segment_ref = ([string]$segment.codex_segment_ref).Replace("__SOURCE_REF_PLACEHOLDER__", $codexSourceRef)
}

$unresolvedCount = @($segments | Where-Object { [string]$_.segment_status -ne "resolved" }).Count
$resolvedCount = @($segments | Where-Object { [string]$_.segment_status -eq "resolved" }).Count
$planStatus = "ready"
if ($segments.Count -eq 0) {
    $planStatus = "need_confirm"
}
elseif ($unresolvedCount -gt 0) {
    $planStatus = "need_confirm"
}
elseif ($resolvedCount -gt 1) {
    $planStatus = "split_required"
}

$reason = "All timestamped Codex events map to one storage binding."
if ($planStatus -eq "split_required") {
    $reason = "Timestamped Codex events cross a binding cutover. Register one B-line 01_session row per resolved segment."
}
elseif ($planStatus -eq "need_confirm") {
    $reason = "Some Codex events have no safe binding, ambiguous binding, or no timestamped events."
}

$questionFields = @()
if ($planStatus -eq "need_confirm") {
    $questionFields = @(Get-HandoverQuestionFields)
}

[ordered]@{
    segment_plan_status = $planStatus
    reason = $reason
    codex_session_ref = $codexSourceRef
    local_jsonl_path = $resolvedSessionPath
    binding_file = $resolvedBindingFile
    binding_rule = "half_open_interval_active_from_inclusive_active_to_exclusive"
    total_lines = $lineCount
    timestamped_event_count = $eventCount
    timestampless_event_count = $timestamplessEvents
    parse_errors = $parseErrors
    first_event_timestamp = if ($null -eq $firstTimestamp) { "" } else { $firstTimestamp.ToString("yyyy-MM-dd HH:mm:ss") }
    last_event_timestamp = if ($null -eq $lastTimestamp) { "" } else { $lastTimestamp.ToString("yyyy-MM-dd HH:mm:ss") }
    question_fields = $questionFields
    segments = $segments
} | ConvertTo-Json -Depth 12

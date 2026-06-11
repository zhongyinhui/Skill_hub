param(
    [Parameter(Mandatory = $true)]
    [string]$SessionId,

    [Parameter(Mandatory = $true)]
    [string]$CustomerId,

    [Parameter(Mandatory = $true)]
    [string]$SalesId,

    [Parameter(Mandatory = $true)]
    [string]$WorkDate,

    [Parameter(Mandatory = $true)]
    [string]$StartSnapshotRef,

    [string]$AStartSnapshot = "",

    [string]$AStartSnapshotFile = "",

    [string]$ExistingFuelTankState = "",

    [string]$ExistingFuelTankStateFile = "",

    [string]$RawInputRefs = "",

    [string]$RawInputRefsFile = "",

    [string]$SalesSupplement = "",

    [string]$SalesSupplementFile = "",

    [string]$CustomerFeedback = "",

    [string]$CustomerFeedbackFile = "",

    [string]$AiAnalysisSummary = "",

    [string]$ExtractedFuelItems = "",

    [string]$ExtractedFuelItemsFile = "",

    [int]$MaxRefs = 100,

    [int]$MaxTextChars = 1200,

    [int]$MaxSnapshotChars = 3000,

    [int]$MaxEvents = 80,

    [switch]$Pretty
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

function Read-OptionalText {
    param(
        [string]$Value,
        [string]$Path
    )

    if (-not [string]::IsNullOrWhiteSpace($Path)) {
        if (-not (Test-Path -LiteralPath $Path)) {
            throw "File does not exist: $Path"
        }
        return [System.IO.File]::ReadAllText((Resolve-Path -LiteralPath $Path).Path, [System.Text.Encoding]::UTF8)
    }
    return $Value
}

function Clip-Text {
    param(
        [object]$Value,
        [int]$Limit
    )

    if ($null -eq $Value) {
        return ""
    }
    $text = [string]$Value
    $text = [regex]::Replace($text, 'data:[^;,\s]+;base64,[A-Za-z0-9+/=]+', 'data:<redacted-base64>')
    $text = $text.Trim()
    if ($text.Length -le $Limit) {
        return $text
    }
    return $text.Substring(0, $Limit)
}

function Get-Sha256Hex {
    param([string]$Value)

    $sha = [System.Security.Cryptography.SHA256]::Create()
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($Value)
    return [BitConverter]::ToString($sha.ComputeHash($bytes)).Replace("-", "").ToLowerInvariant()
}

function Add-IfPresent {
    param(
        [System.Collections.IDictionary]$Target,
        [string]$Name,
        [object]$Value,
        [int]$Limit
    )

    $text = Clip-Text -Value $Value -Limit $Limit
    if (-not [string]::IsNullOrWhiteSpace($text)) {
        $Target[$Name] = $text
    }
}

function New-ContextBlock {
    param(
        [string]$Role,
        [string]$SourceRef,
        [string]$Text,
        [int]$Limit,
        [bool]$Required
    )

    $block = [ordered]@{
        role = $Role
        source_ref = Clip-Text -Value $SourceRef -Limit 500
        available = $false
        content_sha256 = ""
        excerpt = ""
    }

    if (-not [string]::IsNullOrWhiteSpace($Text)) {
        $block["available"] = $true
        $block["content_sha256"] = Get-Sha256Hex -Value $Text
        $block["excerpt"] = Clip-Text -Value $Text -Limit $Limit
    }
    elseif ($Required) {
        throw "$Role is required. Provide AStartSnapshot or AStartSnapshotFile from B-SK02/A-line snapshot loader."
    }

    return $block
}

function ConvertTo-CompactJsonText {
    param([object]$Value)

    if ($null -eq $Value) {
        return ""
    }
    if ($Value -is [string]) {
        return [string]$Value
    }
    return ($Value | ConvertTo-Json -Compress -Depth 20)
}

function Get-ExistingFuelEvents {
    param(
        [string]$ExistingText,
        [int]$Limit
    )

    $result = @()
    if ([string]::IsNullOrWhiteSpace($ExistingText)) {
        return $result
    }

    try {
        $existingObj = $ExistingText | ConvertFrom-Json
        if ($existingObj.fuel_events) {
            $events = @($existingObj.fuel_events)
            foreach ($event in $events) {
                if ($result.Count -ge $Limit) {
                    break
                }
                $result += $event
            }
        }
    }
    catch {
        return $result
    }

    return $result
}

function New-FuelEventId {
    param(
        [string]$SessionIdValue,
        [string]$CustomerIdValue,
        [string]$SalesIdValue,
        [string]$WorkDateValue,
        [string]$RawRefsValue,
        [string]$SalesSupplementValue,
        [string]$CustomerFeedbackValue,
        [string]$AiSummaryValue,
        [string]$ExtractedFuelItemsValue
    )

    $seed = "b.fuel_event.v1|session=$SessionIdValue|customer=$CustomerIdValue|sales=$SalesIdValue|date=$WorkDateValue|raw=$(Get-Sha256Hex -Value $RawRefsValue)|supplement=$(Get-Sha256Hex -Value $SalesSupplementValue)|feedback=$(Get-Sha256Hex -Value $CustomerFeedbackValue)|ai=$(Get-Sha256Hex -Value $AiSummaryValue)|fuel=$(Get-Sha256Hex -Value $ExtractedFuelItemsValue)"
    $hash = (Get-Sha256Hex -Value $seed).Substring(0, 12).ToUpperInvariant()
    $datePart = $WorkDateValue.Replace("-", "")
    return "BFEV-$datePart-$hash"
}

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
if ([string]::IsNullOrWhiteSpace($StartSnapshotRef)) {
    throw "StartSnapshotRef is required."
}
if ($MaxRefs -lt 1 -or $MaxRefs -gt 500) {
    throw "MaxRefs must be between 1 and 500."
}
if ($MaxTextChars -lt 100 -or $MaxTextChars -gt 5000) {
    throw "MaxTextChars must be between 100 and 5000."
}
if ($MaxSnapshotChars -lt 500 -or $MaxSnapshotChars -gt 12000) {
    throw "MaxSnapshotChars must be between 500 and 12000."
}
if ($MaxEvents -lt 1 -or $MaxEvents -gt 500) {
    throw "MaxEvents must be between 1 and 500."
}

$aStartSnapshotText = Read-OptionalText -Value $AStartSnapshot -Path $AStartSnapshotFile
$existingFuelTankText = Read-OptionalText -Value $ExistingFuelTankState -Path $ExistingFuelTankStateFile
$rawRefsText = Read-OptionalText -Value $RawInputRefs -Path $RawInputRefsFile
$salesSupplementText = Read-OptionalText -Value $SalesSupplement -Path $SalesSupplementFile
$customerFeedbackText = Read-OptionalText -Value $CustomerFeedback -Path $CustomerFeedbackFile
$extractedFuelItemsText = Read-OptionalText -Value $ExtractedFuelItems -Path $ExtractedFuelItemsFile

if ([string]::IsNullOrWhiteSpace($rawRefsText) -and
    [string]::IsNullOrWhiteSpace($salesSupplementText) -and
    [string]::IsNullOrWhiteSpace($customerFeedbackText) -and
    [string]::IsNullOrWhiteSpace($AiAnalysisSummary) -and
    [string]::IsNullOrWhiteSpace($extractedFuelItemsText)) {
    throw "Provide session/material fuel input: RawInputRefs, SalesSupplement, CustomerFeedback, AiAnalysisSummary, or ExtractedFuelItems."
}

$lines = @()
if (-not [string]::IsNullOrWhiteSpace($rawRefsText)) {
    foreach ($line in ($rawRefsText -split "\r?\n")) {
        $trimmed = $line.Trim()
        if (-not [string]::IsNullOrWhiteSpace($trimmed)) {
            $lines += $trimmed
        }
    }
}

$materialRefs = @()
$total = 0
foreach ($line in $lines) {
    $total += 1
    if ($materialRefs.Count -ge $MaxRefs) {
        continue
    }

    try {
        $obj = $line | ConvertFrom-Json
        $ref = [ordered]@{}
        Add-IfPresent -Target $ref -Name "material_ref_id" -Value $obj.material_ref_id -Limit 160
        Add-IfPresent -Target $ref -Name "material_type" -Value $obj.material_type -Limit 80
        Add-IfPresent -Target $ref -Name "source_ref" -Value $obj.source_ref -Limit 500
        Add-IfPresent -Target $ref -Name "source_kind" -Value $obj.source_kind -Limit 80
        Add-IfPresent -Target $ref -Name "content_sha256" -Value $obj.content_sha256 -Limit 80
        Add-IfPresent -Target $ref -Name "file_name" -Value $obj.file_name -Limit 200
        Add-IfPresent -Target $ref -Name "file_size" -Value $obj.file_size -Limit 40
        Add-IfPresent -Target $ref -Name "mime_type" -Value $obj.mime_type -Limit 120
        Add-IfPresent -Target $ref -Name "attribution_status" -Value $obj.attribution_status -Limit 80
        Add-IfPresent -Target $ref -Name "captured_at" -Value $obj.captured_at -Limit 80
        Add-IfPresent -Target $ref -Name "summary" -Value $obj.summary -Limit $MaxTextChars
        Add-IfPresent -Target $ref -Name "evidence_note" -Value $obj.evidence_note -Limit $MaxTextChars
        if ($ref.Count -eq 0) {
            $ref["legacy_ref_sha256"] = Get-Sha256Hex -Value $line
            $ref["source_ref"] = Clip-Text -Value $line -Limit 500
        }
        $materialRefs += $ref
    }
    catch {
        $materialRefs += [ordered]@{
            legacy_ref_sha256 = Get-Sha256Hex -Value $line
            source_ref = Clip-Text -Value $line -Limit 500
            parse_status = "legacy_text"
        }
    }
}

$assembledAt = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
$fuelEventId = New-FuelEventId -SessionIdValue $SessionId -CustomerIdValue $CustomerId -SalesIdValue $SalesId -WorkDateValue $WorkDate -RawRefsValue $rawRefsText -SalesSupplementValue $salesSupplementText -CustomerFeedbackValue $customerFeedbackText -AiSummaryValue $AiAnalysisSummary -ExtractedFuelItemsValue $extractedFuelItemsText
$existingEvents = @(Get-ExistingFuelEvents -ExistingText $existingFuelTankText -Limit $MaxEvents)
$fuelEvent = [ordered]@{
    schema = "b.fuel_event.v1"
    fuel_event_id = $fuelEventId
    event_type = "session_material_increment"
    captured_at = $assembledAt
    session_id = $SessionId
    customer_id = $CustomerId
    sales_id = $SalesId
    work_date = $WorkDate
    material_refs = $materialRefs
    raw_input_refs_total = $total
    raw_input_refs_included = $materialRefs.Count
    raw_input_refs_truncated = ($total -gt $materialRefs.Count)
    extracted_fuel_items = Clip-Text -Value $extractedFuelItemsText -Limit $MaxTextChars
    sales_supplement = Clip-Text -Value $salesSupplementText -Limit $MaxTextChars
    customer_feedback = Clip-Text -Value $customerFeedbackText -Limit $MaxTextChars
    ai_analysis_summary_snapshot = Clip-Text -Value $AiAnalysisSummary -Limit $MaxTextChars
}

$knownEventIds = New-Object "System.Collections.Generic.HashSet[string]"
$fuelEvents = @()
foreach ($event in $existingEvents) {
    $eventId = [string]$event.fuel_event_id
    if ([string]::IsNullOrWhiteSpace($eventId)) {
        $eventId = "legacy-" + (Get-Sha256Hex -Value (ConvertTo-CompactJsonText -Value $event)).Substring(0, 12)
    }
    if (-not $knownEventIds.Contains($eventId)) {
        [void]$knownEventIds.Add($eventId)
        $fuelEvents += $event
    }
}
if (-not $knownEventIds.Contains($fuelEventId)) {
    [void]$knownEventIds.Add($fuelEventId)
    $fuelEvents += $fuelEvent
}
if ($fuelEvents.Count -gt $MaxEvents) {
    $fuelEvents = @($fuelEvents | Select-Object -Last $MaxEvents)
}

$output = [ordered]@{
    schema = "b.fuel_tank_inputs.v1"
    mode = "append_only_fuel_deposit"
    assembled_at = $assembledAt
    session_id = $SessionId
    customer_id = $CustomerId
    sales_id = $SalesId
    work_date = $WorkDate
    start_snapshot_ref = $StartSnapshotRef
    a_start_snapshot_context = New-ContextBlock -Role "a_start_snapshot_context" -SourceRef $StartSnapshotRef -Text $aStartSnapshotText -Limit $MaxSnapshotChars -Required $false
    existing_active_fuel_tank_context = New-ContextBlock -Role "existing_active_fuel_tank_context" -SourceRef $SessionId -Text $existingFuelTankText -Limit $MaxSnapshotChars -Required $false
    latest_fuel_event_id = $fuelEventId
    fuel_events_total = $fuelEvents.Count
    fuel_events = $fuelEvents
    raw_input_refs_total = $total
    raw_input_refs_included = $materialRefs.Count
    raw_input_refs_truncated = ($total -gt $materialRefs.Count)
    material_refs = $materialRefs
    extracted_fuel_items = Clip-Text -Value $extractedFuelItemsText -Limit $MaxTextChars
    sales_supplement = Clip-Text -Value $salesSupplementText -Limit $MaxTextChars
    customer_feedback = Clip-Text -Value $customerFeedbackText -Limit $MaxTextChars
    ai_analysis_summary_snapshot = Clip-Text -Value $AiAnalysisSummary -Limit $MaxTextChars
    source_policy = [ordered]@{
        use_refs_only = $true
        no_full_base64 = $true
        no_full_file_body = $true
    }
    deposit_policy = [ordered]@{
        append_only = $true
        each_run_adds_fuel_event = $true
        a_snapshot_optional_context = $true
        primary_sources = @("codex_session", "raw_input_refs", "attachments", "sales_supplement", "customer_feedback")
    }
    judgment_policy = [ordered]@{
        no_fuel_sufficiency = $true
        no_customer_stage = $true
        no_dline_trigger = $true
    }
}

if ($Pretty) {
    $output | ConvertTo-Json -Depth 20
}
else {
    $output | ConvertTo-Json -Compress -Depth 20
}

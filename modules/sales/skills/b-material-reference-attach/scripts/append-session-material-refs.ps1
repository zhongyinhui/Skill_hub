param(
    [string]$BaseToken = "XtSIbjGLSarQHDs3y2ncaWffnze",

    [string]$TableId = "tbl6u4j3HRjz9Ggk",

    [Parameter(Mandatory = $true)]
    [string]$RecordId,

    [string]$ExistingRawInputRefs = "",

    [string]$ExistingRawInputRefsFile = "",

    [string]$ExistingWindowLog = "",

    [string]$ExistingWindowLogFile = "",

    [string]$ExistingAiAnalysisSummary = "",

    [string]$ExistingAiAnalysisSummaryFile = "",

    [string[]]$NewMaterialRef = @(),

    [string]$NewMaterialRefsFile = "",

    [string]$MaterialSummary = "",

    [string]$UpdatedAt = "",

    [ValidateSet("user", "bot")]
    [string]$As = "bot",

    [switch]$UseFieldIds,

    [switch]$AllowEmptyExisting,

    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

if ([string]::IsNullOrWhiteSpace($UpdatedAt)) {
    $UpdatedAt = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
}
else {
    $UpdatedAt = ([datetime]::Parse($UpdatedAt)).ToString("yyyy-MM-dd HH:mm:ss")
}

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

function Split-RefLines {
    param([string]$Value)

    $result = @()
    if ([string]::IsNullOrWhiteSpace($Value)) {
        return $result
    }
    $lines = $Value -split "\r?\n"
    foreach ($line in $lines) {
        $trimmed = $line.Trim()
        if (-not [string]::IsNullOrWhiteSpace($trimmed)) {
            $result += $trimmed
        }
    }
    return $result
}

function Normalize-NewMaterialRefLine {
    param([string]$Line)

    try {
        $obj = $Line | ConvertFrom-Json
    }
    catch {
        throw "New material refs must be valid JSON. Use NewMaterialRefsFile to avoid shell quoting issues."
    }

    if ([string]$obj.schema -ne "b.material_ref.v1") {
        throw "New material ref schema must be b.material_ref.v1."
    }
    if ([string]::IsNullOrWhiteSpace([string]$obj.material_ref_id)) {
        throw "New material ref material_ref_id is required."
    }
    if ([string]::IsNullOrWhiteSpace([string]$obj.source_ref)) {
        throw "New material ref source_ref is required."
    }

    return ($obj | ConvertTo-Json -Compress -Depth 12)
}

function Convert-NewRefsToLines {
    param(
        [string[]]$InlineRefs,
        [string]$Path
    )

    $rawRefs = @()
    foreach ($item in $InlineRefs) {
        if (-not [string]::IsNullOrWhiteSpace($item)) {
            $rawRefs += (Normalize-NewMaterialRefLine -Line $item)
        }
    }
    if (-not [string]::IsNullOrWhiteSpace($Path)) {
        if (-not (Test-Path -LiteralPath $Path)) {
            throw "NewMaterialRefsFile does not exist: $Path"
        }
        $fileText = [System.IO.File]::ReadAllText((Resolve-Path -LiteralPath $Path).Path, [System.Text.Encoding]::UTF8)
        if (-not [string]::IsNullOrWhiteSpace($fileText)) {
            $trimmed = $fileText.Trim()
            if ($trimmed.StartsWith("[")) {
                $items = @($trimmed | ConvertFrom-Json)
                foreach ($obj in $items) {
                    $rawRefs += (Normalize-NewMaterialRefLine -Line ($obj | ConvertTo-Json -Compress -Depth 12))
                }
            }
            else {
                foreach ($line in @(Split-RefLines -Value $fileText)) {
                    $rawRefs += (Normalize-NewMaterialRefLine -Line $line)
                }
            }
        }
    }
    return $rawRefs
}

function Get-DedupeKeys {
    param([string]$Line)

    $keys = @("line:$Line")
    try {
        $obj = $Line | ConvertFrom-Json
        if ($obj.material_ref_id) {
            $keys += "material_ref_id:$([string]$obj.material_ref_id)"
        }
        if ($obj.source_ref) {
            $keys += "source_ref:$([string]$obj.source_ref)"
        }
        if ($obj.content_sha256) {
            $keys += "content_sha256:$([string]$obj.content_sha256)"
        }
    }
    catch {
    }
    return $keys
}

function Has-ConfirmRequired {
    param([string[]]$Lines)

    foreach ($line in $Lines) {
        try {
            $obj = $line | ConvertFrom-Json
            $status = [string]$obj.attribution_status
            if ($status -eq "needs_confirm" -or $status -eq "orphan_candidate") {
                return $true
            }
        }
        catch {
        }
    }
    return $false
}

if ([string]::IsNullOrWhiteSpace($ExistingRawInputRefs) -and [string]::IsNullOrWhiteSpace($ExistingRawInputRefsFile) -and -not $AllowEmptyExisting) {
    throw "ExistingRawInputRefs or ExistingRawInputRefsFile is required unless AllowEmptyExisting is set."
}
if ([string]::IsNullOrWhiteSpace($ExistingWindowLog) -and [string]::IsNullOrWhiteSpace($ExistingWindowLogFile) -and -not $AllowEmptyExisting) {
    throw "ExistingWindowLog or ExistingWindowLogFile is required unless AllowEmptyExisting is set."
}

$existingRaw = Read-OptionalText -Value $ExistingRawInputRefs -Path $ExistingRawInputRefsFile
$existingWindow = Read-OptionalText -Value $ExistingWindowLog -Path $ExistingWindowLogFile
$existingSummary = Read-OptionalText -Value $ExistingAiAnalysisSummary -Path $ExistingAiAnalysisSummaryFile
$existingLines = @(Split-RefLines -Value $existingRaw)
$newLines = @(Convert-NewRefsToLines -InlineRefs $NewMaterialRef -Path $NewMaterialRefsFile)

if ($newLines.Count -eq 0) {
    throw "Provide at least one NewMaterialRef or NewMaterialRefsFile."
}

$knownKeys = New-Object "System.Collections.Generic.HashSet[string]"
$mergedLines = @()
foreach ($line in $existingLines) {
    $mergedLines += $line
    foreach ($key in (Get-DedupeKeys -Line $line)) {
        [void]$knownKeys.Add($key)
    }
}

$addedLines = @()
$duplicateLines = @()
foreach ($line in $newLines) {
    $keys = @(Get-DedupeKeys -Line $line)
    $isDuplicate = $false
    foreach ($key in $keys) {
        if ($knownKeys.Contains($key)) {
            $isDuplicate = $true
            break
        }
    }
    if ($isDuplicate) {
        $duplicateLines += $line
        continue
    }
    $mergedLines += $line
    $addedLines += $line
    foreach ($key in $keys) {
        [void]$knownKeys.Add($key)
    }
}

$humanConfirmRequired = Has-ConfirmRequired -Lines $addedLines
$mergedRaw = ($mergedLines -join "`n")
$logEntry = "[$UpdatedAt] material_attach added=$($addedLines.Count) duplicate=$($duplicateLines.Count) human_confirm_required=$humanConfirmRequired"
if (-not [string]::IsNullOrWhiteSpace($MaterialSummary)) {
    $logEntry = "$logEntry summary=$MaterialSummary"
}

$mergedWindow = $logEntry
if (-not [string]::IsNullOrWhiteSpace($existingWindow)) {
    $mergedWindow = "$existingWindow`n$logEntry"
}

$mergedSummary = $existingSummary
if (-not [string]::IsNullOrWhiteSpace($MaterialSummary)) {
    $summaryEntry = "[$UpdatedAt] $MaterialSummary"
    if ([string]::IsNullOrWhiteSpace($mergedSummary)) {
        $mergedSummary = $summaryEntry
    }
    else {
        $mergedSummary = "$mergedSummary`n$summaryEntry"
    }
}

$FieldMap = [ordered]@{
    raw_input_refs = "fld6oO3sIZ"
    window_log = "fldoGobDEz"
    ai_analysis_summary = "fldNXsP73x"
    updated_at = "fldXP35X3X"
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
Add-FieldValue -Payload $payload -FieldName "raw_input_refs" -Value $mergedRaw
Add-FieldValue -Payload $payload -FieldName "window_log" -Value $mergedWindow
if (-not [string]::IsNullOrWhiteSpace($mergedSummary)) {
    Add-FieldValue -Payload $payload -FieldName "ai_analysis_summary" -Value $mergedSummary
}
Add-FieldValue -Payload $payload -FieldName "updated_at" -Value $UpdatedAt

if ($DryRun) {
    [ordered]@{
        dry_run = $true
        record_id = $RecordId
        base_token = $BaseToken
        table_id = $TableId
        added_count = $addedLines.Count
        duplicate_count = $duplicateLines.Count
        existing_count = $existingLines.Count
        human_confirm_required = $humanConfirmRequired
        payload = $payload
    } | ConvertTo-Json -Depth 12
    return
}

$json = $payload | ConvertTo-Json -Compress -Depth 12
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
        "--record-id", $RecordId,
        "--json", $jsonFileArg,
        "--as", $As
    )

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

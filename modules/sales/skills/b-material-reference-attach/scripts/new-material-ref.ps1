param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("pasted_text", "screenshot", "audio", "file", "transcript", "meeting_note", "codex_turn", "tool_output", "codex_session", "external_link", "feishu_file", "other")]
    [string]$MaterialType,

    [string]$SourceRef = "",

    [string]$LocalPath = "",

    [string]$TextFile = "",

    [string]$Text = "",

    [string]$ExternalUrl = "",

    [string]$FeishuFileToken = "",

    [string]$SessionId = "",

    [string]$CustomerId = "",

    [string]$CapturedBy = "",

    [string]$CapturedAt = "",

    [ValidateSet("session_confirmed", "customer_confirmed", "needs_confirm", "orphan_candidate")]
    [string]$AttributionStatus = "session_confirmed",

    [string]$Summary = "",

    [string]$EvidenceNote = ""
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

function Get-StringSha256 {
    param([string]$Value)

    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($Value)
        $hashBytes = $sha.ComputeHash($bytes)
        return (-join ($hashBytes | ForEach-Object { $_.ToString("x2") }))
    }
    finally {
        $sha.Dispose()
    }
}

function Get-FileSha256 {
    param([string]$Path)

    $stream = [System.IO.File]::Open($Path, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $hashBytes = $sha.ComputeHash($stream)
        return (-join ($hashBytes | ForEach-Object { $_.ToString("x2") }))
    }
    finally {
        $sha.Dispose()
        $stream.Close()
    }
}

if ([string]::IsNullOrWhiteSpace($CapturedAt)) {
    $CapturedAt = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
}
else {
    $CapturedAt = ([datetime]::Parse($CapturedAt)).ToString("yyyy-MM-dd HH:mm:ss")
}

$contentHash = ""
$fileName = ""
$fileSize = 0
$sourceKind = "runtime"
$resolvedLocalPath = ""
$textLength = 0

if ([string]::IsNullOrWhiteSpace($LocalPath) -and $SourceRef -like "local-file:*") {
    throw "Use LocalPath instead of a bare local-file SourceRef so the script can compute file hash and size."
}

if (-not [string]::IsNullOrWhiteSpace($LocalPath)) {
    if (-not (Test-Path -LiteralPath $LocalPath)) {
        throw "LocalPath does not exist: $LocalPath"
    }
    $resolvedLocalPath = (Resolve-Path -LiteralPath $LocalPath).Path
    $fileInfo = Get-Item -LiteralPath $resolvedLocalPath
    $contentHash = Get-FileSha256 -Path $resolvedLocalPath
    $fileName = $fileInfo.Name
    $fileSize = $fileInfo.Length
    $sourceKind = "local_file"
    if ([string]::IsNullOrWhiteSpace($SourceRef)) {
        $SourceRef = "local-file:$resolvedLocalPath"
    }
}
elseif (-not [string]::IsNullOrWhiteSpace($TextFile)) {
    if (-not (Test-Path -LiteralPath $TextFile)) {
        throw "TextFile does not exist: $TextFile"
    }
    $resolvedLocalPath = (Resolve-Path -LiteralPath $TextFile).Path
    $textValue = [System.IO.File]::ReadAllText($resolvedLocalPath, [System.Text.Encoding]::UTF8)
    $contentHash = Get-StringSha256 -Value $textValue
    $fileInfo = Get-Item -LiteralPath $resolvedLocalPath
    $fileName = $fileInfo.Name
    $fileSize = $fileInfo.Length
    $textLength = $textValue.Length
    $sourceKind = "text_file"
    if ([string]::IsNullOrWhiteSpace($SourceRef)) {
        $SourceRef = "local-text-file:$resolvedLocalPath"
    }
}
elseif (-not [string]::IsNullOrWhiteSpace($Text)) {
    $contentHash = Get-StringSha256 -Value $Text
    $textLength = $Text.Length
    $sourceKind = "pasted_text"
    if ([string]::IsNullOrWhiteSpace($SourceRef)) {
        throw "SourceRef is required when using inline Text, usually codex-session:<id>#turn:<n>."
    }
}
elseif (-not [string]::IsNullOrWhiteSpace($ExternalUrl)) {
    $contentHash = Get-StringSha256 -Value $ExternalUrl
    $sourceKind = "external_link"
    if ([string]::IsNullOrWhiteSpace($SourceRef)) {
        $SourceRef = "external-url:$ExternalUrl"
    }
}
elseif (-not [string]::IsNullOrWhiteSpace($FeishuFileToken)) {
    $contentHash = Get-StringSha256 -Value $FeishuFileToken
    $sourceKind = "feishu_file"
    if ([string]::IsNullOrWhiteSpace($SourceRef)) {
        $SourceRef = "feishu-file-token:$FeishuFileToken"
    }
}
elseif (-not [string]::IsNullOrWhiteSpace($SourceRef)) {
    $contentHash = Get-StringSha256 -Value $SourceRef
    if ($SourceRef -like "codex-session:*") {
        $sourceKind = "codex"
    }
}
else {
    throw "Provide SourceRef, LocalPath, TextFile, Text with SourceRef, ExternalUrl, or FeishuFileToken."
}

if ([string]::IsNullOrWhiteSpace($SourceRef)) {
    throw "SourceRef could not be resolved."
}

$idBasis = "$MaterialType|$SourceRef|$contentHash|$CapturedAt"
$idHash = (Get-StringSha256 -Value $idBasis).Substring(0, 8)
$materialRefId = "mref-$(([datetime]::Parse($CapturedAt)).ToString('yyyyMMddHHmmss'))-$idHash"

[ordered]@{
    schema = "b.material_ref.v1"
    material_ref_id = $materialRefId
    material_type = $MaterialType
    source_ref = $SourceRef
    source_kind = $sourceKind
    content_sha256 = $contentHash
    file_name = $fileName
    file_size = $fileSize
    text_length = $textLength
    captured_at = $CapturedAt
    captured_by = $CapturedBy
    session_id = $SessionId
    customer_id = $CustomerId
    attribution_status = $AttributionStatus
    summary = $Summary
    evidence_note = $EvidenceNote
} | ConvertTo-Json -Compress -Depth 8

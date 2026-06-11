param(
    [Parameter(Mandatory = $true)]
    [string]$SalesId,

    [Parameter(Mandatory = $true)]
    [string]$WorkDate,

    [Parameter(Mandatory = $true)]
    [string]$CodexSourceRef,

    [string]$BLineKnowledgeBaseKey = "",

    [string]$Prefix = "BSES"
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

if ([string]::IsNullOrWhiteSpace($SalesId)) {
    throw "SalesId is required."
}
if ($WorkDate -notmatch '^\d{4}-\d{2}-\d{2}$') {
    throw "WorkDate must be an absolute date in yyyy-MM-dd format."
}
if ([string]::IsNullOrWhiteSpace($CodexSourceRef)) {
    throw "CodexSourceRef is required."
}

function Get-Hash {
    param([string]$Value, [int]$Length = 10)
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($Value)
        $hashBytes = $sha.ComputeHash($bytes)
        $hash = -join ($hashBytes | ForEach-Object { $_.ToString("x2") })
        return $hash.Substring(0, [Math]::Min($Length, $hash.Length))
    }
    finally {
        $sha.Dispose()
    }
}

function Get-Slug {
    param([string]$Value, [string]$FallbackPrefix, [int]$MaxLength = 18)
    $slug = $Value.ToLowerInvariant() -replace '[^a-z0-9]+', ''
    if ([string]::IsNullOrWhiteSpace($slug)) {
        $slug = "$FallbackPrefix$(Get-Hash -Value $Value -Length 6)"
    }
    if ($slug.Length -gt $MaxLength) {
        $slug = $slug.Substring(0, $MaxLength)
    }
    return $slug
}

if ([string]::IsNullOrWhiteSpace($BLineKnowledgeBaseKey)) {
    $BLineKnowledgeBaseKey = "default-bline-kb"
}

$dateSlug = $WorkDate -replace '[^0-9]', ''
$salesSlug = Get-Slug -Value $SalesId -FallbackPrefix "sales"
$codexSlug = "codex$(Get-Hash -Value $CodexSourceRef -Length 10)"
$basis = "$SalesId|$WorkDate|$BLineKnowledgeBaseKey|$CodexSourceRef"
$hash = Get-Hash -Value $basis -Length 10
$sessionId = "$Prefix-$dateSlug-$salesSlug-$codexSlug-$hash"

[ordered]@{
    session_id = $sessionId
    idempotency_basis = $basis
    sales_id = $SalesId
    work_date = $WorkDate
    bline_knowledge_base_key = $BLineKnowledgeBaseKey
    codex_source_ref = $CodexSourceRef
} | ConvertTo-Json -Depth 4

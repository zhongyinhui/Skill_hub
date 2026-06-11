param(
    [Parameter(Mandatory = $true)]
    [string]$SessionPath,

    [string]$SessionId = "",

    [string]$CapturedBy = "",

    [string]$CustomerId = "",

    [ValidateSet("session_confirmed", "customer_confirmed", "needs_confirm", "orphan_candidate")]
    [string]$AttributionStatus = "session_confirmed",

    [switch]$IncludeUserText,

    [switch]$IncludeLoosePaths,

    [int]$MaxRefs = 1000,

    [int]$MaxUserTextRefs = 20
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

if (-not (Test-Path -LiteralPath $SessionPath)) {
    throw "SessionPath does not exist: $SessionPath"
}
if ($MaxUserTextRefs -lt 0 -or $MaxUserTextRefs -gt 500) {
    throw "MaxUserTextRefs must be between 0 and 500."
}
if ($MaxRefs -lt 1 -or $MaxRefs -gt 10000) {
    throw "MaxRefs must be between 1 and 10000."
}

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

function Get-BytesSha256 {
    param([byte[]]$Bytes)

    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $hashBytes = $sha.ComputeHash($Bytes)
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

function Convert-ToLocalTimeString {
    param([string]$Value)

    if ([string]::IsNullOrWhiteSpace($Value)) {
        return (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    }
    try {
        return ([datetimeoffset]::Parse($Value)).LocalDateTime.ToString("yyyy-MM-dd HH:mm:ss")
    }
    catch {
        return ([datetime]::Parse($Value)).ToString("yyyy-MM-dd HH:mm:ss")
    }
}

function New-MaterialRef {
    param(
        [string]$MaterialType,
        [string]$SourceRef,
        [string]$SourceKind,
        [string]$ContentHash,
        [string]$CapturedAt,
        [string]$Summary,
        [string]$EvidenceNote,
        [string]$FileName = "",
        [int64]$FileSize = 0,
        [int64]$TextLength = 0,
        [string]$MimeType = "",
        [string]$LocalPath = "",
        [int]$LineNumber = 0,
        [int]$ContentIndex = 0
    )

    $basis = "$MaterialType|$SourceRef|$ContentHash|$CapturedAt"
    $idHash = (Get-StringSha256 -Value $basis).Substring(0, 8)
    $materialRefId = "mref-$(([datetime]::Parse($CapturedAt)).ToString('yyyyMMddHHmmss'))-$idHash"

    return [ordered]@{
        schema = "b.material_ref.v1"
        material_ref_id = $materialRefId
        material_type = $MaterialType
        source_ref = $SourceRef
        source_kind = $SourceKind
        content_sha256 = $ContentHash
        file_name = $FileName
        file_size = $FileSize
        text_length = $TextLength
        mime_type = $MimeType
        local_path = $LocalPath
        codex_line = $LineNumber
        codex_content_index = $ContentIndex
        captured_at = $CapturedAt
        captured_by = $CapturedBy
        session_id = $SessionId
        customer_id = $CustomerId
        attribution_status = $AttributionStatus
        summary = $Summary
        evidence_note = $EvidenceNote
    }
}

function Get-TextFileMentions {
    param(
        [string]$Text,
        [bool]$IncludeLoose
    )

    $mentions = @()
    if ([string]::IsNullOrWhiteSpace($Text)) {
        return $mentions
    }

    $patterns = @(
        '##\s+.+?:\s+(?<path>[A-Za-z]:[\\/][^\r\n]+)'
    )
    if ($IncludeLoose) {
        $patterns += '(?<path>[A-Za-z]:[\\/][^\r\n`"<>|]+)'
    }

    foreach ($pattern in $patterns) {
        $matches = [regex]::Matches($Text, $pattern)
        foreach ($match in $matches) {
            $path = [string]$match.Groups["path"].Value
            $path = $path.Trim()
            if (-not [string]::IsNullOrWhiteSpace($path)) {
                $mentions += $path
            }
        }
    }
    return @($mentions | Select-Object -Unique)
}

$resolvedPath = (Resolve-Path -LiteralPath $SessionPath).Path
$refs = @()
$parseErrors = 0
$lineNo = 0
$userTextRefCount = 0
$codexSessionId = ""
$seenSourceRefs = New-Object "System.Collections.Generic.HashSet[string]"
$seenMentionKeys = New-Object "System.Collections.Generic.HashSet[string]"

$stream = [System.IO.File]::Open($resolvedPath, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
$reader = New-Object System.IO.StreamReader($stream, [System.Text.Encoding]::UTF8)
try {
    while (($line = $reader.ReadLine()) -ne $null) {
        $lineNo++
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

        if ($obj.type -eq "session_meta" -and $obj.payload -and $obj.payload.id) {
            $codexSessionId = [string]$obj.payload.id
            if ([string]::IsNullOrWhiteSpace($SessionId)) {
                $SessionId = $codexSessionId
            }
        }

        $capturedAt = Convert-ToLocalTimeString -Value ([string]$obj.timestamp)
        $payloadType = [string]$obj.payload.type
        $role = [string]$obj.payload.role
        $contentItems = @()

        if ($obj.payload -and $obj.payload.content) {
            $contentItems = @($obj.payload.content)
        }

        for ($i = 0; $i -lt $contentItems.Count; $i++) {
            $content = $contentItems[$i]
            $contentType = [string]$content.type
            $sourceRefPrefix = ""
            if (-not [string]::IsNullOrWhiteSpace($codexSessionId)) {
                $sourceRefPrefix = "codex-session:$codexSessionId"
            }
            else {
                $sourceRefPrefix = "local-codex-session-jsonl:$resolvedPath"
            }

            if ($contentType -eq "input_image") {
                if ($refs.Count -ge $MaxRefs) {
                    break
                }
                $imageUrl = [string]$content.image_url
                if ([string]::IsNullOrWhiteSpace($imageUrl)) {
                    continue
                }

                $mimeType = ""
                $hash = Get-StringSha256 -Value $imageUrl
                $size = $imageUrl.Length
                if ($imageUrl -match '^data:(?<mime>[^;]+);base64,(?<data>.+)$') {
                    $mimeType = [string]$Matches["mime"]
                    $bytes = [System.Convert]::FromBase64String([string]$Matches["data"])
                    $hash = Get-BytesSha256 -Bytes $bytes
                    $size = $bytes.Length
                }

                $sourceRef = "$sourceRefPrefix#line:$lineNo#content:$i"
                if ($seenSourceRefs.Add($sourceRef)) {
                    $refs += New-MaterialRef `
                        -MaterialType "screenshot" `
                        -SourceRef $sourceRef `
                        -SourceKind "codex_inline_image" `
                        -ContentHash $hash `
                        -CapturedAt $capturedAt `
                        -Summary "Codex input_image from session line $lineNo" `
                        -EvidenceNote "Inline image is stored in the Codex session JSONL; raw base64 is not copied into 01_session." `
                        -FileSize $size `
                        -MimeType $mimeType `
                        -LineNumber $lineNo `
                        -ContentIndex $i
                }
            }

            if ($contentType -eq "input_text" -and $role -eq "user") {
                $text = [string]$content.text
                foreach ($mentionedPath in @(Get-TextFileMentions -Text $text -IncludeLoose ([bool]$IncludeLoosePaths))) {
                    if ($refs.Count -ge $MaxRefs) {
                        break
                    }

                    $mentionKey = ($mentionedPath.Trim()).ToLowerInvariant()
                    if (-not $seenMentionKeys.Add($mentionKey)) {
                        continue
                    }

                    $sourceRef = "$sourceRefPrefix#line:$lineNo#mentioned-file:$($refs.Count + 1)"
                    if (-not $seenSourceRefs.Add($sourceRef)) {
                        continue
                    }

                    $fileName = ""
                    $fileSize = 0
                    $hash = Get-StringSha256 -Value $mentionedPath
                    $sourceKind = "codex_mentioned_file"
                    $evidenceNote = "File path was mentioned in a user message; file was not verified on disk."
                    $localPath = $mentionedPath
                    try {
                        if (Test-Path -LiteralPath $mentionedPath) {
                            $resolvedMention = (Resolve-Path -LiteralPath $mentionedPath).Path
                            $fileInfo = Get-Item -LiteralPath $resolvedMention -ErrorAction Stop
                            $fileName = $fileInfo.Name
                            $localPath = $resolvedMention
                            if ($fileInfo.PSIsContainer) {
                                $sourceKind = "codex_mentioned_directory"
                                $hash = Get-StringSha256 -Value $resolvedMention
                                $evidenceNote = "Directory path was mentioned in a user message and verified on disk."
                            }
                            else {
                                $fileSize = $fileInfo.Length
                                $hash = Get-FileSha256 -Path $resolvedMention
                                $evidenceNote = "File path was mentioned in a user message and verified on disk."
                            }
                        }
                    }
                    catch {
                        $evidenceNote = "Path was mentioned in a user message but could not be opened safely."
                    }

                    $refs += New-MaterialRef `
                        -MaterialType "file" `
                        -SourceRef $sourceRef `
                        -SourceKind $sourceKind `
                        -ContentHash $hash `
                        -CapturedAt $capturedAt `
                        -Summary "File mentioned by user message at session line $lineNo" `
                        -EvidenceNote $evidenceNote `
                        -FileName $fileName `
                        -FileSize $fileSize `
                        -LocalPath $localPath `
                        -LineNumber $lineNo `
                        -ContentIndex $i
                }

                if ($IncludeUserText -and $userTextRefCount -lt $MaxUserTextRefs -and -not [string]::IsNullOrWhiteSpace($text)) {
                    if ($refs.Count -ge $MaxRefs) {
                        break
                    }
                    $sourceRef = "$sourceRefPrefix#line:$lineNo#content:$i"
                    if ($seenSourceRefs.Add($sourceRef)) {
                        $hash = Get-StringSha256 -Value $text
                        $refs += New-MaterialRef `
                            -MaterialType "pasted_text" `
                            -SourceRef $sourceRef `
                            -SourceKind "codex_user_text" `
                            -ContentHash $hash `
                            -CapturedAt $capturedAt `
                            -Summary "User text from Codex session line $lineNo" `
                            -EvidenceNote "Full text remains in Codex session JSONL; 01_session stores only a reference and hash." `
                            -TextLength $text.Length `
                            -LineNumber $lineNo `
                            -ContentIndex $i
                        $userTextRefCount++
                    }
                }
            }
        }

        if ($refs.Count -ge $MaxRefs) {
            break
        }
    }
}
finally {
    $reader.Close()
    $stream.Close()
}

foreach ($ref in $refs) {
    $ref | ConvertTo-Json -Compress -Depth 12
}

if ($refs.Count -eq 0) {
    [Console]::Error.WriteLine("No session material refs found. parse_errors=$parseErrors")
}

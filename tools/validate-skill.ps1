param(
    [string]$Root = (Resolve-Path "$PSScriptRoot\..").Path
)

$ErrorActionPreference = "Stop"
$failed = $false

function Fail {
    param([string]$Message)
    Write-Host "FAIL $Message" -ForegroundColor Red
    $script:failed = $true
}

function Pass {
    param([string]$Message)
    Write-Host "PASS $Message" -ForegroundColor Green
}

function Test-Version {
    param([string]$Version)
    return $Version -match '^\d+\.\d+\.\d+$'
}

$skillsRoot = Join-Path $Root "skills"
if (-not (Test-Path $skillsRoot)) {
    Fail "Missing skills directory: $skillsRoot"
    exit 1
}

$skillDirs = Get-ChildItem -Path $skillsRoot -Directory
if ($skillDirs.Count -eq 0) {
    Fail "No skill directories found under skills/"
    exit 1
}

foreach ($skill in $skillDirs) {
    $relative = "skills/$($skill.Name)"
    $skillMd = Join-Path $skill.FullName "SKILL.md"
    $readme = Join-Path $skill.FullName "README.md"
    $versionFile = Join-Path $skill.FullName "VERSION"
    $changelog = Join-Path $skill.FullName "CHANGELOG.md"

    foreach ($required in @($skillMd, $readme, $versionFile, $changelog)) {
        if (-not (Test-Path $required)) {
            Fail "$relative is missing $(Split-Path $required -Leaf)"
        }
    }

    if (Test-Path $skillMd) {
        $content = Get-Content -Raw -Encoding UTF8 $skillMd
        if ($content -notmatch '(?s)^---\s.*?\bname:\s*\S+.*?---') {
            Fail "$relative/SKILL.md is missing frontmatter name"
        }
        if ($content -notmatch '(?s)^---\s.*?\bdescription:\s*.+?.*?---') {
            Fail "$relative/SKILL.md is missing frontmatter description"
        }
    }

    if (Test-Path $versionFile) {
        $version = (Get-Content -Raw -Encoding UTF8 $versionFile).Trim()
        if (-not (Test-Version $version)) {
            Fail "$relative/VERSION must use MAJOR.MINOR.PATCH, found '$version'"
        }
        elseif (Test-Path $changelog) {
            $changelogText = Get-Content -Raw -Encoding UTF8 $changelog
            if ($changelogText -notmatch [regex]::Escape("## $version")) {
                Fail "$relative/CHANGELOG.md does not contain an entry for $version"
            }
        }
    }
}

$blockedPatterns = @("*.log", "*.tmp", "*.bak", ".env", ".env.*")
foreach ($pattern in $blockedPatterns) {
    $matches = Get-ChildItem -Path $Root -Recurse -Force -File -Filter $pattern |
        Where-Object { $_.FullName -notmatch '\\.git\\' }
    foreach ($match in $matches) {
        Fail "Do not commit local or temporary file: $($match.FullName.Substring($Root.Length + 1))"
    }
}

if ($failed) {
    Write-Host "Skill validation failed." -ForegroundColor Red
    exit 1
}

Pass "All skill checks passed."


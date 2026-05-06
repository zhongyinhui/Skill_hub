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

function Test-SkillDirectory {
    param(
        [System.IO.DirectoryInfo]$Skill,
        [string]$Relative
    )

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

$modulesRoot = Join-Path $Root "modules"
if (-not (Test-Path $modulesRoot)) {
    Fail "Missing modules directory: $modulesRoot"
    exit 1
}

$requiredModules = @("_shared", "customer-success", "sales", "ip", "private-domain", "hr")
foreach ($moduleName in $requiredModules) {
    $modulePath = Join-Path $modulesRoot $moduleName
    $moduleReadme = Join-Path $modulePath "README.md"
    $moduleSkills = Join-Path $modulePath "skills"

    if (-not (Test-Path $modulePath)) {
        Fail "Missing required module: modules/$moduleName"
        continue
    }
    if (-not (Test-Path $moduleReadme)) {
        Fail "modules/$moduleName is missing README.md"
    }
    if (-not (Test-Path $moduleSkills)) {
        Fail "modules/$moduleName is missing skills directory"
    }
}

$skillDirs = @()
$moduleDirs = Get-ChildItem -Path $modulesRoot -Directory
foreach ($module in $moduleDirs) {
    $moduleSkillsRoot = Join-Path $module.FullName "skills"
    if (Test-Path $moduleSkillsRoot) {
        $skillDirs += Get-ChildItem -Path $moduleSkillsRoot -Directory | ForEach-Object {
            [PSCustomObject]@{
                Directory = $_
                Relative = "modules/$($module.Name)/skills/$($_.Name)"
            }
        }
    }
}

if ($skillDirs.Count -eq 0) {
    Fail "No skill directories found under modules/*/skills/"
}

foreach ($entry in $skillDirs) {
    Test-SkillDirectory -Skill $entry.Directory -Relative $entry.Relative
}

$templateSkill = Join-Path $Root "templates\skill"
if (-not (Test-Path $templateSkill)) {
    Fail "Missing skill template: templates/skill"
}
else {
    Test-SkillDirectory -Skill (Get-Item $templateSkill) -Relative "templates/skill"
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

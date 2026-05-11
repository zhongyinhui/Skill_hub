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

function Test-AsciiSlug {
    param([string]$Value)
    return $Value -match '^[a-z0-9][a-z0-9-]*$'
}

function Test-ModuleId {
    param([string]$Value)
    return $Value -eq "_shared" -or (Test-AsciiSlug $Value)
}

function Test-SkillDirectory {
    param(
        [System.IO.DirectoryInfo]$Skill,
        [string]$Relative
    )

    if (($Relative -like "modules/*" -or $Relative -like ".codex/skills/*") -and -not (Test-AsciiSlug $Skill.Name)) {
        Fail "$relative directory name must use lowercase pinyin/English ASCII, digits, and hyphens only"
    }

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
        $nameMatch = [regex]::Match($content, '(?m)^name:\s*["'']?([^"''\r\n]+)["'']?\s*$')
        if (-not $nameMatch.Success) {
            Fail "$relative/SKILL.md is missing frontmatter name"
        }
        else {
            $frontmatterName = $nameMatch.Groups[1].Value.Trim()
            if (-not (Test-AsciiSlug $frontmatterName)) {
                Fail "$relative/SKILL.md frontmatter name must use lowercase pinyin/English ASCII, digits, and hyphens only"
            }
            if (($Relative -like "modules/*" -or $Relative -like ".codex/skills/*") -and $frontmatterName -ne $Skill.Name) {
                Fail "$relative/SKILL.md frontmatter name '$frontmatterName' must match directory name '$($Skill.Name)'"
            }
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
    if (-not (Test-ModuleId $module.Name)) {
        Fail "Module directory '$($module.Name)' must use _shared or lowercase pinyin/English ASCII, digits, and hyphens only"
    }

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

$codexSkillsRoot = Join-Path $Root ".codex\skills"
if (Test-Path $codexSkillsRoot) {
    Get-ChildItem -Path $codexSkillsRoot -Directory | ForEach-Object {
        Test-SkillDirectory -Skill $_ -Relative ".codex/skills/$($_.Name)"
    }
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

$workflowRoot = Join-Path $Root ".github\workflows"
if (Test-Path $workflowRoot) {
    $workflowFiles = @()
    $workflowFiles += Get-ChildItem -Path (Join-Path $workflowRoot "*.yml") -File -ErrorAction SilentlyContinue
    $workflowFiles += Get-ChildItem -Path (Join-Path $workflowRoot "*.yaml") -File -ErrorAction SilentlyContinue
    foreach ($workflow in $workflowFiles) {
        $relativeWorkflow = $workflow.FullName.Substring($Root.Length + 1).Replace("\", "/")
        $lines = Get-Content -Encoding UTF8 $workflow.FullName
        for ($i = 0; $i -lt $lines.Count; $i++) {
            if ($lines[$i] -match '^\s*name:\s*(.+?)\s*$') {
                $nameValue = $matches[1].Trim('"').Trim("'")
                if ($nameValue -cmatch '[^\x00-\x7F]') {
                    Fail "$relativeWorkflow line $($i + 1) has non-ASCII GitHub Actions name '$nameValue'; use English ASCII to keep branch protection checks stable."
                }
            }
        }
    }
}

if ($failed) {
    Write-Host "Skill validation failed." -ForegroundColor Red
    exit 1
}

Pass "All skill checks passed."

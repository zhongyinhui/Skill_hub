param(
    [Parameter(Mandatory = $true)]
    [string]$ModuleId,

    [Parameter(Mandatory = $true)]
    [string]$SkillName
)

$ErrorActionPreference = "Stop"
$root = (Resolve-Path "$PSScriptRoot\..").Path
$skillDir = Join-Path $root "modules\$ModuleId\skills\$SkillName"
$versionFile = Join-Path $skillDir "VERSION"

if (-not (Test-Path $skillDir)) {
    throw "Skill not found: modules/$ModuleId/skills/$SkillName"
}

if (-not (Test-Path $versionFile)) {
    throw "Missing VERSION for modules/$ModuleId/skills/$SkillName"
}

$version = (Get-Content -Raw -Encoding UTF8 $versionFile).Trim()
if ($version -notmatch '^\d+\.\d+\.\d+$') {
    throw "Invalid VERSION '$version'. Expected MAJOR.MINOR.PATCH."
}

& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $root "tools\validate-skill.ps1")
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

$tag = "$ModuleId/$SkillName/v$version"
$existingTag = git tag --list $tag
if ($existingTag) {
    throw "Tag already exists: $tag"
}

Write-Host "Ready to release $ModuleId/$SkillName as $tag"
Write-Host "Create the tag with:"
Write-Host "  git tag $tag"
Write-Host "  git push origin $tag"

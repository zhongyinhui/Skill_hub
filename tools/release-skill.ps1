param(
    [Parameter(Mandatory = $true)]
    [string]$SkillName
)

$ErrorActionPreference = "Stop"
$root = (Resolve-Path "$PSScriptRoot\..").Path
$skillDir = Join-Path $root "skills\$SkillName"
$versionFile = Join-Path $skillDir "VERSION"

if (-not (Test-Path $skillDir)) {
    throw "Skill not found: skills/$SkillName"
}

if (-not (Test-Path $versionFile)) {
    throw "Missing VERSION for skills/$SkillName"
}

$version = (Get-Content -Raw -Encoding UTF8 $versionFile).Trim()
if ($version -notmatch '^\d+\.\d+\.\d+$') {
    throw "Invalid VERSION '$version'. Expected MAJOR.MINOR.PATCH."
}

powershell -ExecutionPolicy Bypass -File (Join-Path $root "tools\validate-skill.ps1")

$tag = "$SkillName/v$version"
$existingTag = git tag --list $tag
if ($existingTag) {
    throw "Tag already exists: $tag"
}

Write-Host "Ready to release $SkillName as $tag"
Write-Host "Create the tag with:"
Write-Host "  git tag $tag"
Write-Host "  git push origin $tag"


param(
    [string]$Root = (Resolve-Path "$PSScriptRoot\..").Path,
    [string]$SkillName,
    [switch]$Clean
)

$ErrorActionPreference = "Stop"

function Test-AsciiSlug {
    param([string]$Value)
    return $Value -match '^[a-z0-9][a-z0-9-]*$'
}

$modulesRoot = Join-Path $Root "modules"
$targetRoot = Join-Path $Root ".codex\skills"

if (-not (Test-Path $modulesRoot)) {
    throw "Missing modules directory: $modulesRoot"
}

if (-not (Test-Path $targetRoot)) {
    New-Item -ItemType Directory -Path $targetRoot -Force | Out-Null
}

$formalSkills = Get-ChildItem -Path $modulesRoot -Directory | ForEach-Object {
    $module = $_
    $skillsRoot = Join-Path $module.FullName "skills"
    if (Test-Path $skillsRoot) {
        Get-ChildItem -Path $skillsRoot -Directory | ForEach-Object {
            [PSCustomObject]@{
                Module = $module.Name
                Name = $_.Name
                Path = $_.FullName
            }
        }
    }
}

if ($SkillName) {
    if (-not (Test-AsciiSlug $SkillName)) {
        throw "SkillName must use lowercase pinyin/English ASCII, digits, and hyphens only: $SkillName"
    }
    $formalSkills = $formalSkills | Where-Object { $_.Name -eq $SkillName }
    if (-not $formalSkills) {
        throw "Cannot find formal skill named '$SkillName' under modules/*/skills/"
    }
}

foreach ($skill in $formalSkills) {
    $target = Join-Path $targetRoot $skill.Name
    if ((Test-Path $target) -and $Clean) {
        $resolvedTarget = (Resolve-Path -LiteralPath $target).Path
        $resolvedRoot = (Resolve-Path -LiteralPath $targetRoot).Path
        if (-not $resolvedTarget.StartsWith($resolvedRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
            throw "Refusing to remove path outside target root: $resolvedTarget"
        }
        Remove-Item -LiteralPath $target -Recurse -Force
    }
    if (-not (Test-Path $target)) {
        New-Item -ItemType Directory -Path $target -Force | Out-Null
    }

    foreach ($item in Get-ChildItem -LiteralPath $skill.Path -Force) {
        $dest = Join-Path $target $item.Name
        if (Test-Path $dest) {
            Remove-Item -LiteralPath $dest -Recurse -Force
        }
        Copy-Item -LiteralPath $item.FullName -Destination $dest -Recurse -Force
    }

    Write-Host "SYNC $($skill.Module)/$($skill.Name) -> project callable entry .codex/skills/$($skill.Name)" -ForegroundColor Green
}

Write-Host "Done. If a project skill is not visible as `$<skill-name>, start a new Codex thread or refresh the skill list." -ForegroundColor Cyan

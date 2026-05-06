param(
    [string]$Root = (Resolve-Path "$PSScriptRoot\..").Path,
    [string]$OutputDir = "dist/module-zips"
)

$ErrorActionPreference = "Stop"

$rootPath = (Resolve-Path $Root).Path
if ([System.IO.Path]::IsPathRooted($OutputDir)) {
    $outputPath = $OutputDir
}
else {
    $outputPath = Join-Path $rootPath $OutputDir
}

$outputFullPath = [System.IO.Path]::GetFullPath($outputPath)
if (-not $outputFullPath.StartsWith($rootPath, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "OutputDir must stay inside repository root: $outputFullPath"
}

$modulesRoot = Join-Path $rootPath "modules"
if (-not (Test-Path -LiteralPath $modulesRoot)) {
    throw "Missing modules directory: $modulesRoot"
}

if (Test-Path -LiteralPath $outputFullPath) {
    Remove-Item -LiteralPath $outputFullPath -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $outputFullPath | Out-Null

$tempBase = $env:RUNNER_TEMP
if (-not $tempBase) {
    $tempBase = [System.IO.Path]::GetTempPath()
}
$tempRoot = Join-Path $tempBase ("skill-hub-module-zips-" + [System.Guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Force -Path $tempRoot | Out-Null

try {
    $moduleDirs = Get-ChildItem -LiteralPath $modulesRoot -Directory | Sort-Object Name
    if ($moduleDirs.Count -eq 0) {
        throw "No modules found under modules/"
    }

    foreach ($module in $moduleDirs) {
        $moduleReadme = Join-Path $module.FullName "README.md"
        $moduleSkills = Join-Path $module.FullName "skills"

        if (-not (Test-Path -LiteralPath $moduleReadme)) {
            throw "Module $($module.Name) is missing README.md"
        }
        if (-not (Test-Path -LiteralPath $moduleSkills)) {
            throw "Module $($module.Name) is missing skills directory"
        }

        $stagingModule = Join-Path $tempRoot $module.Name
        $stagingSkills = Join-Path $stagingModule "skills"
        New-Item -ItemType Directory -Force -Path $stagingSkills | Out-Null

        Copy-Item -LiteralPath $moduleReadme -Destination $stagingModule
        $skillItems = Get-ChildItem -LiteralPath $moduleSkills -Force
        foreach ($item in $skillItems) {
            Copy-Item -LiteralPath $item.FullName -Destination $stagingSkills -Recurse -Force
        }

        $zipPath = Join-Path $outputFullPath "$($module.Name)-skills.zip"
        Compress-Archive -Path $stagingModule -DestinationPath $zipPath -Force
        Write-Host "PACKAGED $($module.Name) -> $zipPath"
    }
}
finally {
    if (Test-Path -LiteralPath $tempRoot) {
        Remove-Item -LiteralPath $tempRoot -Recurse -Force
    }
}


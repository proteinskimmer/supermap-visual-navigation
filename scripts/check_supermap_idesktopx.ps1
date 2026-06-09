param(
    [string]$InstallRoot = "E:\supermap_software\SuperMap iDesktopX 2025"
)

$ErrorActionPreference = "Stop"

function Test-RequiredPath {
    param(
        [string]$Path,
        [string]$Label
    )

    if (Test-Path -LiteralPath $Path) {
        Write-Host "[OK] $Label => $Path"
        return $true
    }

    Write-Host "[FAIL] $Label => $Path"
    return $false
}

$allOk = $true

$requiredPaths = @(
    @{ Label = "Install root"; Path = $InstallRoot },
    @{ Label = "Main executable"; Path = Join-Path $InstallRoot "SuperMap iDesktopX.exe" },
    @{ Label = "Startup script"; Path = Join-Path $InstallRoot "startup.bat" },
    @{ Label = "iDesktop jar"; Path = Join-Path $InstallRoot "iDesktop.jar" },
    @{ Label = "Core bin"; Path = Join-Path $InstallRoot "bin" },
    @{ Label = "Bundled JRE"; Path = Join-Path $InstallRoot "jre\bin\java.exe" },
    @{ Label = "Configuration"; Path = Join-Path $InstallRoot "configuration" },
    @{ Label = "Help"; Path = Join-Path $InstallRoot "help\SuperMap iDesktopX Help.chm" },
    @{ Label = "User manual"; Path = Join-Path $InstallRoot "SuperMap iDesktopX UserManual.pdf" },
    @{ Label = "Installation guide"; Path = Join-Path $InstallRoot "InstallationGuide.pdf" },
    @{ Label = "Readme"; Path = Join-Path $InstallRoot "readme.html" },
    @{ Label = "What is new"; Path = Join-Path $InstallRoot "What_is_new.html" },
    @{ Label = "Sample data"; Path = Join-Path $InstallRoot "sampleData" },
    @{ Label = "3D CBD workspace"; Path = Join-Path $InstallRoot "sampleData\3D\CBDDataset\CBD.smwu" },
    @{ Label = "3D CBD UDB"; Path = Join-Path $InstallRoot "sampleData\3D\CBDDataset\CBD.udb" },
    @{ Label = "WebMap China workspace"; Path = Join-Path $InstallRoot "sampleData\WebMap\China100\China100.smwu" }
)

foreach ($item in $requiredPaths) {
    $allOk = (Test-RequiredPath -Path $item.Path -Label $item.Label) -and $allOk
}

$keyBinFiles = @(
    "com.supermap.data.jar",
    "com.supermap.mapping.jar",
    "com.supermap.realspace.jar",
    "com.supermap.data.conversion.jar",
    "com.supermap.analyst.spatialanalyst.jar",
    "com.supermap.analyst.terrainanalyst.jar",
    "com.supermap.licensemanager.jar",
    "WrapjRealspace.dll",
    "SuScene.dll",
    "SuCacheBuilder3D.dll",
    "SuToolkit3DTiles.dll"
)

foreach ($fileName in $keyBinFiles) {
    $path = Join-Path (Join-Path $InstallRoot "bin") $fileName
    $allOk = (Test-RequiredPath -Path $path -Label "Core component $fileName") -and $allOk
}

$versionPath = Join-Path $InstallRoot "bin\VERSION"
if (Test-Path -LiteralPath $versionPath) {
    $version = Get-Content -LiteralPath $versionPath -TotalCount 1
    Write-Host "[INFO] bin/VERSION: $version"
}

$javaPath = Join-Path $InstallRoot "jre\bin\java.exe"
if (Test-Path -LiteralPath $javaPath) {
    Write-Host "[INFO] Bundled Java:"
    & $javaPath -version
}

$sampleData = Join-Path $InstallRoot "sampleData"
if (Test-Path -LiteralPath $sampleData) {
    $sampleSummary = Get-ChildItem -LiteralPath $sampleData -Recurse -File |
        Group-Object Extension |
        Sort-Object Count -Descending |
        Select-Object Count, Name
    Write-Host "[INFO] Sample data extension summary:"
    $sampleSummary | Format-Table -AutoSize
}

$readme = Join-Path $InstallRoot "readme.html"
if (Test-Path -LiteralPath $readme) {
    $trialLine = Select-String -Path $readme -Encoding UTF8 -Pattern "90" -SimpleMatch -List
    if ($trialLine) {
        Write-Host "[OK] Trial license note marker found in readme.html"
    }
    else {
        Write-Host "[WARN] Trial license marker not found by text search"
    }
}

if (-not $allOk) {
    throw "iDesktopX local installation verification failed. Some required paths are missing."
}

Write-Host "[PASS] iDesktopX local package appears complete. GUI sample-data verification still requires manual screenshot evidence."


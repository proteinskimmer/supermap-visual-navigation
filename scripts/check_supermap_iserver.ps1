param(
    [string]$InstallRoot = "E:\supermap_software\supermap-iserver-2025u1a-windows-x64-all",
    [int]$Port = 8090
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

function Test-HttpUrl {
    param(
        [string]$Url
    )

    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 15
        Write-Host "[OK] HTTP $($response.StatusCode) => $Url"
    }
    catch {
        Write-Host "[WARN] HTTP check failed => $Url :: $($_.Exception.Message)"
    }
}

$allOk = $true

$requiredPaths = @(
    @{ Label = "Install root"; Path = $InstallRoot },
    @{ Label = "iServer entry"; Path = Join-Path $InstallRoot "bin\iserver.bat" },
    @{ Label = "Startup script"; Path = Join-Path $InstallRoot "bin\startup.bat" },
    @{ Label = "Shutdown script"; Path = Join-Path $InstallRoot "bin\shutdown.bat" },
    @{ Label = "Server config"; Path = Join-Path $InstallRoot "conf\server.xml" },
    @{ Label = "iServer webapp"; Path = Join-Path $InstallRoot "webapps\iserver" },
    @{ Label = "Docs"; Path = Join-Path $InstallRoot "docs" },
    @{ Label = "Samples"; Path = Join-Path $InstallRoot "samples\data" },
    @{ Label = "Realspace CBD sample"; Path = Join-Path $InstallRoot "samples\data\Realspace\CBD\CBD.sxwu" },
    @{ Label = "Bundled JRE"; Path = Join-Path $InstallRoot "support\jre\bin\java.exe" },
    @{ Label = "Objects Java"; Path = Join-Path $InstallRoot "support\objectsjava\bin\com.supermap.data.jar" },
    @{ Label = "License Center"; Path = Join-Path $InstallRoot "support\SuperMapLicenseCenter\SuperMap.LicenseCenter(for .NET 4.0).exe" },
    @{ Label = "iClient3D bundled"; Path = Join-Path $InstallRoot "iClient\for3D\webgl\zh\Build\SuperMap3D\SuperMap3D.js" }
)

foreach ($item in $requiredPaths) {
    $allOk = (Test-RequiredPath -Path $item.Path -Label $item.Label) -and $allOk
}

$serverXml = Join-Path $InstallRoot "conf\server.xml"
if (Test-Path -LiteralPath $serverXml) {
    $connector = Select-String -Path $serverXml -Pattern "Connector port=`"$Port`"" -SimpleMatch -List
    if ($connector) {
        Write-Host "[OK] server.xml contains HTTP connector port $Port"
    }
    else {
        Write-Host "[WARN] server.xml does not contain expected HTTP connector port $Port"
    }
}

$versionPath = Join-Path $InstallRoot "support\objectsjava\bin\VERSION"
if (Test-Path -LiteralPath $versionPath) {
    $version = Get-Content -LiteralPath $versionPath -TotalCount 1
    Write-Host "[INFO] objectsjava VERSION: $version"
}

$javaPath = Join-Path $InstallRoot "support\jre\bin\java.exe"
if (Test-Path -LiteralPath $javaPath) {
    Write-Host "[INFO] Bundled Java:"
    & $javaPath -version
}

$listening = netstat -ano | Select-String ":$Port"
if ($listening) {
    Write-Host "[OK] Port $Port appears in netstat:"
    $listening | ForEach-Object { Write-Host "     $($_.Line.Trim())" }
    Test-HttpUrl "http://localhost:$Port/iserver"
    Test-HttpUrl "http://localhost:$Port/iserver/services"
    Test-HttpUrl "http://localhost:$Port/iserver/admin-ui/services/serviceManagement"
    Test-HttpUrl "http://localhost:$Port/iserver/help"
}
else {
    Write-Host "[WARN] Port $Port is not listening. Start iServer from the bin directory with: iserver.bat -start"
}

if (-not $allOk) {
    throw "iServer local installation verification failed. Some required paths are missing."
}

Write-Host "[PASS] iServer local package appears complete. Runtime verification depends on port $Port listening and HTTP checks above."


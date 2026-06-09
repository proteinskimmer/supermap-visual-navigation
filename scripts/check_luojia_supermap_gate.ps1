param(
  [string]$IServerBaseUrl = "http://localhost:8090/iserver",
  [string]$BackendBaseUrl = "http://localhost:8000/api"
)

$ErrorActionPreference = "Stop"

function Get-JsonOrNull {
  param([string]$Url, [string]$Label)

  try {
    $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 20
    if ($response.StatusCode -ne 200) {
      Write-Host "[TODO] $Label => HTTP $($response.StatusCode)"
      return $null
    }
    Write-Host "[OK] $Label => HTTP 200"
    return $response.Content | ConvertFrom-Json
  }
  catch {
    Write-Host "[TODO] $Label => $Url"
    Write-Host "       $($_.Exception.Message)"
    return $null
  }
}

$map = Get-JsonOrNull -Url "$IServerBaseUrl/services/map-luojia_mountain_demo/rest/maps.json" -Label "map-luojia_mountain_demo maps"
$data = Get-JsonOrNull -Url "$IServerBaseUrl/services/data-luojia_mountain_demo/rest/data/datasources.json" -Label "data-luojia_mountain_demo datasources"
$scene = Get-JsonOrNull -Url "$IServerBaseUrl/services/3D-luojia_mountain_demo/rest/realspace/scenes.json" -Label "3D-luojia_mountain_demo scenes"

$failed = $false
if ($null -eq $map) { $failed = $true }
if ($null -eq $data) { $failed = $true }
if ($null -eq $scene) { $failed = $true }

if ($null -ne $scene) {
  $payload = $scene | ConvertTo-Json -Depth 10
  if ($payload -match "luojia_mountain_demo") {
    Write-Host "[OK] scenes payload contains luojia_mountain_demo"
  }
  else {
    Write-Host "[TODO] scenes payload does not contain luojia_mountain_demo"
    $failed = $true
  }
}

if ($failed) {
  Write-Host "[FAIL] Luojia SuperMap service gate is not complete."
  exit 2
}

Write-Host "[PASS] Luojia SuperMap service gate verified."

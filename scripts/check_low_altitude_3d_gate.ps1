param(
  [string]$IServerBaseUrl = "http://localhost:8090/iserver",
  [string]$BackendBaseUrl = "http://localhost:8000/api",
  [string]$SceneServiceName = "3D-low_altitude_demo",
  [string]$ExpectedSceneName = "low_altitude_demo"
)

$ErrorActionPreference = "Stop"

function Get-JsonOrNull {
  param([string]$Url, [string]$Label)

  try {
    $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 10
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

Write-Host "== Backend scene config =="
$backend = Get-JsonOrNull -Url "$BackendBaseUrl/supermap/services" -Label "backend /api/supermap/services"
if ($null -ne $backend -and $backend.success) {
  $scene = @($backend.data | Where-Object { $_.id -eq "scene" }) | Select-Object -First 1
  if ($scene) {
    Write-Host "[INFO] backend scene name: $($scene.name)"
    Write-Host "[INFO] backend scene status: $($scene.status)"
    if ($scene.name -eq $SceneServiceName -and $scene.status -eq "verified") {
      Write-Host "[OK] backend points to verified project-owned scene"
    }
    else {
      Write-Host "[TODO] backend is not yet pointing to verified $SceneServiceName"
    }
  }
}

Write-Host ""
Write-Host "== iServer project-owned 3D service =="
$scenesUrl = "$IServerBaseUrl/services/$SceneServiceName/rest/realspace/scenes.json"
$scenes = Get-JsonOrNull -Url $scenesUrl -Label "$SceneServiceName scenes.json"
if ($null -eq $scenes) {
  Write-Host ""
  Write-Host "[NEXT] Publish project-owned 3D service first, then re-run this gate."
  exit 2
}

$payload = $scenes | ConvertTo-Json -Depth 10
if ($payload -match [regex]::Escape($ExpectedSceneName)) {
  Write-Host "[OK] scenes payload contains expected scene marker: $ExpectedSceneName"
  Write-Host "[PASS] project-owned 3D service gate verified"
  exit 0
}

Write-Host "[TODO] $SceneServiceName exists, but expected scene marker was not found: $ExpectedSceneName"
exit 3

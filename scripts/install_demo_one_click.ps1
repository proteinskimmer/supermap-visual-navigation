param(
  [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")),
  [string]$EnvName = "supermap_nav",
  [string]$CondaExe = "",
  [string]$IClient3DRoot = "",
  [string]$IServerRoot = "",
  [switch]$NoNetwork,
  [switch]$SkipConda,
  [switch]$SkipNpm,
  [switch]$SkipSdk,
  [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"

function Write-Step {
  param([string]$Message)
  Write-Host ""
  Write-Host "== $Message =="
}

function Write-Ok {
  param([string]$Message)
  Write-Host "[OK] $Message"
}

function Write-Warn {
  param([string]$Message)
  Write-Host "[WARN] $Message"
}

function Resolve-FirstExistingPath {
  param([string[]]$Candidates)
  foreach ($candidate in $Candidates) {
    if ($candidate -and (Test-Path -LiteralPath $candidate)) {
      return (Resolve-Path -LiteralPath $candidate).Path
    }
  }
  return ""
}

function Resolve-ProjectRootPath {
  param([string]$Path)
  $rawPath = if ($null -eq $Path) { "" } else { [string]$Path }
  $cleanPath = $rawPath.Trim().Trim('"').Trim("'")
  if (-not $cleanPath) {
    throw "ProjectRoot is empty."
  }
  return (Resolve-Path -LiteralPath $cleanPath).Path.TrimEnd("\", "/")
}

function Resolve-CommandPath {
  param([string]$Name)
  $command = Get-Command $Name -ErrorAction SilentlyContinue | Select-Object -First 1
  if ($command) {
    return $command.Source
  }
  return ""
}

function Assert-Executable {
  param([string]$Path, [string]$Label)
  if (-not ($Path -and (Test-Path -LiteralPath $Path))) {
    throw "$Label not found. Install it first or pass an explicit path."
  }
  Write-Ok "$Label => $Path"
}

function Test-CondaEnvExists {
  param([string]$Conda, [string]$Name)
  $envList = & $Conda env list 2>$null
  if ($LASTEXITCODE -ne 0) {
    throw "Failed to list conda environments with $Conda"
  }
  return [bool]($envList | Select-String -Pattern "^\s*$([regex]::Escape($Name))\s+")
}

function Find-SuperMapRoot {
  param([string]$ExplicitPath, [string[]]$Candidates, [string]$RequiredRelativePath)
  if ($ExplicitPath) {
    if (Test-Path -LiteralPath (Join-Path $ExplicitPath $RequiredRelativePath)) {
      return (Resolve-Path -LiteralPath $ExplicitPath).Path
    }
    throw "SuperMap path is invalid: $ExplicitPath"
  }
  foreach ($candidate in $Candidates) {
    if (Test-Path -LiteralPath (Join-Path $candidate $RequiredRelativePath)) {
      return (Resolve-Path -LiteralPath $candidate).Path
    }
  }
  return ""
}

$ProjectRoot = Resolve-ProjectRootPath -Path $ProjectRoot
$FrontendDir = Join-Path $ProjectRoot "frontend"
$EnvironmentFile = Join-Path $ProjectRoot "environment.yml"
$PackageLock = Join-Path $FrontendDir "package-lock.json"
$NodeModules = Join-Path $FrontendDir "node_modules"
$SdkTarget = Join-Path $FrontendDir "public\vendor\supermap3d\Build\SuperMap3D\SuperMap3D.js"

Set-Location $ProjectRoot

Write-Host "== SuperMap Visual Navigation Demo Installer =="
Write-Host "[INFO] Project root: $ProjectRoot"
if ($NoNetwork) {
  Write-Warn "NoNetwork mode enabled. The script will only use existing local dependencies."
}

Write-Step "Basic project files"
if (-not (Test-Path -LiteralPath $EnvironmentFile)) {
  throw "Missing environment.yml: $EnvironmentFile"
}
if (-not (Test-Path -LiteralPath $PackageLock)) {
  throw "Missing frontend package-lock.json: $PackageLock"
}
Write-Ok "environment.yml"
Write-Ok "frontend package-lock.json"

Write-Step "Python environment"
if ($SkipConda) {
  Write-Warn "Skipped conda environment setup."
}
else {
  if (-not $CondaExe) {
    $CondaExe = Resolve-FirstExistingPath @(
      "E:\anaconda\Scripts\conda.exe",
      "E:\miniconda3\Scripts\conda.exe",
      "C:\ProgramData\anaconda3\Scripts\conda.exe",
      "C:\ProgramData\miniconda3\Scripts\conda.exe",
      (Join-Path $env:USERPROFILE "anaconda3\Scripts\conda.exe"),
      (Join-Path $env:USERPROFILE "miniconda3\Scripts\conda.exe"),
      (Resolve-CommandPath "conda.exe")
    )
  }
  Assert-Executable -Path $CondaExe -Label "conda.exe"
  $envExists = Test-CondaEnvExists -Conda $CondaExe -Name $EnvName
  if ($envExists) {
    if ($NoNetwork) {
      Write-Ok "conda env exists: $EnvName"
    }
    else {
      Write-Host "[RUN] conda env update -n $EnvName -f environment.yml --prune"
      & $CondaExe env update -n $EnvName -f $EnvironmentFile --prune
      if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
      Write-Ok "conda env updated: $EnvName"
    }
  }
  else {
    if ($NoNetwork) {
      throw "conda env does not exist in NoNetwork mode: $EnvName"
    }
    Write-Host "[RUN] conda env create -f environment.yml"
    & $CondaExe env create -f $EnvironmentFile
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    Write-Ok "conda env created: $EnvName"
  }
}

Write-Step "Node.js and frontend dependencies"
$NodeExe = Resolve-CommandPath "node.exe"
$NpmCmd = Resolve-CommandPath "npm.cmd"
Assert-Executable -Path $NodeExe -Label "node.exe"
Assert-Executable -Path $NpmCmd -Label "npm.cmd"
Set-Location $FrontendDir
& $NodeExe --version
if ($SkipNpm) {
  Write-Warn "Skipped npm dependency setup."
}
elseif ((Test-Path -LiteralPath $NodeModules) -and $NoNetwork) {
  Write-Ok "frontend node_modules exists"
}
elseif ($NoNetwork) {
  throw "frontend node_modules missing in NoNetwork mode: $NodeModules"
}
else {
  Write-Host "[RUN] npm ci"
  & $NpmCmd ci
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
  Write-Ok "frontend dependencies installed"
}
if (-not $SkipBuild) {
  Write-Host "[RUN] npm run build"
  & $NpmCmd run build
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
  Write-Ok "frontend build passed"
}

Set-Location $ProjectRoot

Write-Step "SuperMap iClient3D SDK"
if ($SkipSdk) {
  Write-Warn "Skipped iClient3D SDK copy."
}
elseif (Test-Path -LiteralPath $SdkTarget) {
  Write-Ok "iClient3D SDK already prepared under frontend/public/vendor"
}
else {
  $IClient3DRoot = Find-SuperMapRoot `
    -ExplicitPath $IClient3DRoot `
    -RequiredRelativePath "Build\SuperMap3D\SuperMap3D.js" `
    -Candidates @(
      "E:\supermap_software\supermap-iclient3d-for-webgl_webgpu-2025u1",
      "D:\supermap_software\supermap-iclient3d-for-webgl_webgpu-2025u1",
      "C:\supermap_software\supermap-iclient3d-for-webgl_webgpu-2025u1"
    )
  if (-not $IClient3DRoot) {
    throw "iClient3D SDK not found. Pass -IClient3DRoot or copy SDK resources to frontend/public/vendor/supermap3d."
  }
  & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $ProjectRoot "scripts\prepare_iclient3d_public.ps1") -SdkRoot $IClient3DRoot
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

Write-Step "SuperMap iServer"
$IServerRoot = Find-SuperMapRoot `
  -ExplicitPath $IServerRoot `
  -RequiredRelativePath "bin\startup.bat" `
  -Candidates @(
    "E:\supermap_software\supermap-iserver-2025u1a-windows-x64-all",
    "D:\supermap_software\supermap-iserver-2025u1a-windows-x64-all",
    "C:\supermap_software\supermap-iserver-2025u1a-windows-x64-all"
  )
if ($IServerRoot) {
  Write-Ok "iServer root => $IServerRoot"
}
else {
  Write-Warn "iServer root not found automatically. START_DEMO can still work if iServer is already running at http://localhost:8090/iserver."
}

Write-Step "Runtime check"
if (-not (Test-Path -LiteralPath (Join-Path $ProjectRoot "supermap_file_root"))) {
  Write-Warn "supermap_file_root missing. Project SuperMap services may need republishing on this computer."
}
else {
  Write-Ok "supermap_file_root exists"
}
if (-not (Test-Path -LiteralPath (Join-Path $ProjectRoot "config\supermap_services.local.json"))) {
  Write-Warn "config\supermap_services.local.json missing. Copy an example config, fill local service URLs and optional Tianditu token before final demo."
}
else {
  Write-Ok "SuperMap service config exists"
}

Write-Host ""
Write-Host "[PASS] Install preparation finished."
Write-Host "Next:"
Write-Host "  1. If this is a new computer, open iServer once and confirm the file root/service publication."
Write-Host "  2. Double-click START_DEMO.bat."
Write-Host "  3. Open http://localhost:5173 if the browser does not open automatically."

param(
  [string]$InstallRoot = "E:\supermap_software\SuperMap iDesktopX 2025",
  [string]$ProjectRoot = "E:\supermap_project",
  [string]$Workspace = "supermap_file_root\luojia_workspace\luojia_mountain_demo.smwu",
  [string]$SceneName = "luojia_mountain_demo",
  [string]$DatasourceAlias = "luojia_mountain_demo"
)

$ErrorActionPreference = "Stop"

function Require-Path {
  param([string]$Path, [string]$Label)
  if (-not (Test-Path -LiteralPath $Path)) {
    throw "$Label not found: $Path"
  }
}

$workspacePath = Join-Path $ProjectRoot $Workspace
$workspaceDir = Split-Path -Parent $workspacePath
$javaSource = Join-Path $ProjectRoot "scripts\CreateLuojiaScene.java"
$classesDir = Join-Path $ProjectRoot ".tmp\luojia_scene_builder_classes"
$javac = "C:\Program Files\Microsoft\jdk-21.0.9.10-hotspot\bin\javac.exe"
$java = "C:\Program Files\Microsoft\jdk-21.0.9.10-hotspot\bin\java.exe"
$summaryPath = Join-Path $workspaceDir "build_3d_scene_summary.txt"

Require-Path -Path $InstallRoot -Label "SuperMap iDesktopX install root"
Require-Path -Path $workspacePath -Label "Luojia workspace"
Require-Path -Path $javaSource -Label "Luojia Java scene builder source"
Require-Path -Path $javac -Label "javac"
Require-Path -Path $java -Label "java"

New-Item -ItemType Directory -Force -Path $classesDir | Out-Null

$classpath = "$classesDir;$(Join-Path $InstallRoot 'bin\*')"

Write-Host "[COMPILE] CreateLuojiaScene.java"
& $javac -encoding UTF-8 -cp $classpath -d $classesDir $javaSource
if ($LASTEXITCODE -ne 0) {
  throw "javac failed with exit code $LASTEXITCODE"
}

$env:Path = "$(Join-Path $InstallRoot 'bin');$(Join-Path $InstallRoot 'jre\bin');$env:Path"

Write-Host "[RUN] build Luojia 3D scene => $workspacePath"
Push-Location (Join-Path $InstallRoot "bin")
try {
  $output = & $java `
    "-Djava.library.path=$(Join-Path $InstallRoot 'bin')" `
    -cp $classpath `
    CreateLuojiaScene `
    $workspacePath `
    $SceneName `
    $DatasourceAlias
  $output | Tee-Object -FilePath $summaryPath
  if ($LASTEXITCODE -ne 0) {
    throw "java scene builder failed with exit code $LASTEXITCODE"
  }
}
finally {
  Pop-Location
}

Write-Host "[OK] Luojia 3D scene written into: $workspacePath"
Write-Host "[OK] summary: $summaryPath"

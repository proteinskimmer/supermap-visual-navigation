param(
  [string]$InstallRoot = "E:\supermap_software\SuperMap iDesktopX 2025",
  [string]$ProjectRoot = "E:\supermap_project",
  [string]$SourceWorkspace = "supermap_file_root\demo_workspace\low_altitude_demo.smwu",
  [string]$OutputDir = "supermap_file_root\demo_workspace_3d_auto",
  [string]$SceneName = "low_altitude_demo",
  [switch]$Overwrite
)

$ErrorActionPreference = "Stop"

function Require-Path {
  param([string]$Path, [string]$Label)
  if (-not (Test-Path -LiteralPath $Path)) {
    throw "$Label not found: $Path"
  }
}

$sourceWorkspacePath = Join-Path $ProjectRoot $SourceWorkspace
$sourceDir = Split-Path -Parent $sourceWorkspacePath
$outputRoot = Join-Path $ProjectRoot $OutputDir
$outputWorkspace = Join-Path $outputRoot "low_altitude_demo.smwu"
$javaSource = Join-Path $ProjectRoot "scripts\CreateLowAltitudeSceneProbe.java"
$classesDir = Join-Path $ProjectRoot ".tmp\scene_builder_classes"
$javac = "C:\Program Files\Microsoft\jdk-21.0.9.10-hotspot\bin\javac.exe"
$java = "C:\Program Files\Microsoft\jdk-21.0.9.10-hotspot\bin\java.exe"
$summaryPath = Join-Path $outputRoot "build_3d_scene_summary.txt"

Require-Path -Path $InstallRoot -Label "SuperMap iDesktopX install root"
Require-Path -Path $sourceWorkspacePath -Label "source workspace"
Require-Path -Path (Join-Path $sourceDir "low_altitude_demo.udbx") -Label "source datasource"
Require-Path -Path $javaSource -Label "Java scene builder source"
Require-Path -Path $javac -Label "javac"
Require-Path -Path $java -Label "java"

if ((Test-Path -LiteralPath $outputRoot) -and -not $Overwrite) {
  throw "Output directory already exists: $outputRoot. Re-run with -Overwrite."
}

Remove-Item -LiteralPath $outputRoot -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $outputRoot | Out-Null
New-Item -ItemType Directory -Force -Path $classesDir | Out-Null

Copy-Item -LiteralPath $sourceWorkspacePath -Destination $outputWorkspace -Force
Get-ChildItem -Path $sourceDir -Filter "low_altitude_demo.*" -File |
  Where-Object { $_.FullName -ne $sourceWorkspacePath } |
  ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $outputRoot $_.Name) -Force
  }

$classpath = "$classesDir;$(Join-Path $InstallRoot 'bin\*')"

Write-Host "[COMPILE] CreateLowAltitudeSceneProbe.java"
& $javac -encoding UTF-8 -cp $classpath -d $classesDir $javaSource

$env:Path = "$(Join-Path $InstallRoot 'bin');$(Join-Path $InstallRoot 'jre\bin');$env:Path"

Write-Host "[RUN] build 3D scene workspace => $outputWorkspace"
Push-Location (Join-Path $InstallRoot "bin")
try {
  $output = & $java `
    "-Djava.library.path=$(Join-Path $InstallRoot 'bin')" `
    -cp $classpath `
    CreateLowAltitudeSceneProbe `
    $outputWorkspace `
    $SceneName
  $output | Tee-Object -FilePath $summaryPath
}
finally {
  Pop-Location
}

Write-Host "[OK] 3D scene workspace created: $outputWorkspace"
Write-Host "[OK] summary: $summaryPath"

param(
  [string]$InstallRoot = "E:\supermap_software\SuperMap iDesktopX 2025",
  [string]$ProjectRoot = "E:\supermap_project",
  [string]$SourceWorkspace = "supermap_file_root\demo_workspace\low_altitude_demo.smwu",
  [string]$ProbeDir = ".tmp\scene_probe",
  [string]$SceneName = "low_altitude_demo"
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
$probeRoot = Join-Path $ProjectRoot $ProbeDir
$probeWorkspace = Join-Path $probeRoot "low_altitude_demo.smwu"
$javaSource = Join-Path $ProjectRoot "scripts\CreateLowAltitudeSceneProbe.java"
$classesDir = Join-Path $probeRoot "classes"
$javac = "C:\Program Files\Microsoft\jdk-21.0.9.10-hotspot\bin\javac.exe"
$java = "C:\Program Files\Microsoft\jdk-21.0.9.10-hotspot\bin\java.exe"

Require-Path -Path $InstallRoot -Label "SuperMap iDesktopX install root"
Require-Path -Path $sourceWorkspacePath -Label "source workspace"
Require-Path -Path (Join-Path $sourceDir "low_altitude_demo.udbx") -Label "source datasource"
Require-Path -Path $javaSource -Label "Java probe source"
Require-Path -Path $javac -Label "javac"
Require-Path -Path $java -Label "java"

Remove-Item -LiteralPath $probeRoot -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $probeRoot | Out-Null
New-Item -ItemType Directory -Force -Path $classesDir | Out-Null

Copy-Item -LiteralPath $sourceWorkspacePath -Destination $probeWorkspace -Force
Get-ChildItem -Path $sourceDir -Filter "low_altitude_demo.*" -File |
  Where-Object { $_.FullName -ne $sourceWorkspacePath } |
  ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $probeRoot $_.Name) -Force
  }

$classpath = "$classesDir;$(Join-Path $InstallRoot 'bin\*')"

Write-Host "[COMPILE] CreateLowAltitudeSceneProbe.java"
& $javac -encoding UTF-8 -cp $classpath -d $classesDir $javaSource

$env:Path = "$(Join-Path $InstallRoot 'bin');$(Join-Path $InstallRoot 'jre\bin');$env:Path"

Write-Host "[RUN] probe workspace => $probeWorkspace"
Push-Location (Join-Path $InstallRoot "bin")
try {
  & $java `
    "-Djava.library.path=$(Join-Path $InstallRoot 'bin')" `
    -cp $classpath `
    CreateLowAltitudeSceneProbe `
    $probeWorkspace `
    $SceneName
}
finally {
  Pop-Location
}

Write-Host "[OK] probe completed. Workspace copy: $probeWorkspace"

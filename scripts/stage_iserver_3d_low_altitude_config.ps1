param(
  [string]$InstallRoot = "E:\supermap_software\supermap-iserver-2025u1a-windows-x64-all",
  [string]$ProjectRoot = "E:\supermap_project",
  [string]$SceneServiceName = "3D-low_altitude_demo",
  [string]$WorkspacePathInIServer = '${fileManagerWorkDir}/demo_workspace/low_altitude_demo.smwu',
  [string]$OutputDir = "docs\supermap_integration\generated"
)

$ErrorActionPreference = "Stop"

$sourceXml = Join-Path $InstallRoot "webapps\iserver\WEB-INF\iserver-services.xml"
if (-not (Test-Path -LiteralPath $sourceXml)) {
  throw "iServer services XML not found: $sourceXml"
}

$outputRoot = Join-Path $ProjectRoot $OutputDir
New-Item -ItemType Directory -Force -Path $outputRoot | Out-Null

$stagedXml = Join-Path $outputRoot "iserver-services.with-3D-low_altitude_demo.staged.xml"
$summaryPath = Join-Path $outputRoot "iserver_3d_low_altitude_stage_summary.json"

$original = Get-Content -LiteralPath $sourceXml -Raw -Encoding UTF8
if ($original -match [regex]::Escape($SceneServiceName)) {
  Write-Host "[INFO] $SceneServiceName already appears in source iServer config."
}

$component = @"
    <component alias="$SceneServiceName" class="com.supermap.services.components.impl.RealspaceImpl" enabled="true" initOnCreate="false" initPriority="0" instanceCount="0" interfaceNames="rest" name="$SceneServiceName" providers="$SceneServiceName">
      <config class="com.supermap.services.components.RealspaceConfig"/>
    </component>
"@

$provider = @"
    <provider class="com.supermap.services.providers.UGCRealspaceProvider" enabled="true" name="$SceneServiceName">
      <config class="com.supermap.services.providers.UGCRealspaceProviderSetting">
        <workspacePath>$WorkspacePathInIServer</workspacePath>
        <xmlParse>false</xmlParse>
        <publishAllDatasets>false</publishAllDatasets>
        <output>./output</output>
        <isMultiInstance>false</isMultiInstance>
      </config>
    </provider>
"@

$escapedServiceName = [regex]::Escape($SceneServiceName)
$componentPattern = "(?s)\s*<component\b[^>]*(?:alias|name)=`"$escapedServiceName`"[^>]*>.*?</component>"
$providerPattern = "(?s)\s*<provider\b[^>]*name=`"$escapedServiceName`"[^>]*>.*?</provider>"

$staged = [regex]::Replace($original, $componentPattern, "")
$staged = [regex]::Replace($staged, $providerPattern, "")
$staged = $staged -replace '(?s)(\s*</components>)', "`r`n$component`r`n`$1"
$staged = $staged -replace '(?s)(\s*</providers>)', "`r`n$provider`r`n`$1"

Set-Content -LiteralPath $stagedXml -Value $staged -Encoding UTF8
[xml]$null = Get-Content -LiteralPath $stagedXml -Raw -Encoding UTF8

$summary = [ordered]@{
  generated_at = (Get-Date).ToString("s")
  source_xml = $sourceXml
  staged_xml = $stagedXml
  scene_service_name = $SceneServiceName
  workspace_path_in_iserver = $WorkspacePathInIServer
  strict_status = "staged only; not applied to iServer. Applying requires backup, controlled merge, restart, and REST gate."
  next_gate = "Run scripts/check_low_altitude_3d_gate.ps1 after controlled publish."
}

$summary | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $summaryPath -Encoding UTF8

Write-Host "[OK] staged iServer 3D config XML => $stagedXml"
Write-Host "[OK] staged XML is well formed"
Write-Host "[OK] summary => $summaryPath"
Write-Host "[WARN] This script did not modify iServer. 3D-low_altitude_demo remains unverified until applied and REST-checked."

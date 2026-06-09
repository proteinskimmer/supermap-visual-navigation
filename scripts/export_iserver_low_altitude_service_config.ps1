param(
  [string]$ProjectRoot = "E:\supermap_project",
  [string]$WorkspacePathInIServer = '${fileManagerWorkDir}/demo_workspace/low_altitude_demo.smwu',
  [string]$MapServiceName = "map-low_altitude_demo",
  [string]$DataServiceName = "data-low_altitude_demo",
  [string]$SceneServiceName = "3D-low_altitude_demo",
  [string]$OutputDir = "docs\supermap_integration\generated",
  [switch]$IncludeUnverified3D
)

$ErrorActionPreference = "Stop"

$outputRoot = Join-Path $ProjectRoot $OutputDir
New-Item -ItemType Directory -Force -Path $outputRoot | Out-Null

$mapDataFragmentPath = Join-Path $outputRoot "low_altitude_demo_map_data_iserver_services_fragment.xml"
$fullDraftPath = Join-Path $outputRoot "low_altitude_demo_iserver_services_draft.xml"
$sceneFragmentPath = Join-Path $outputRoot "low_altitude_demo_3d_unverified_fragment.xml"
$summaryPath = Join-Path $outputRoot "low_altitude_demo_iserver_config_summary.json"

$mapDataFragment = @"
<!-- low_altitude_demo map/data service components -->
<component alias="$MapServiceName" class="com.supermap.services.components.impl.MapImpl" enabled="true" initOnCreate="false" initPriority="0" instanceCount="0" interfaceNames="rest" name="$MapServiceName" providers="$MapServiceName">
  <config class="com.supermap.services.components.MapConfig">
    <useCache>true</useCache>
    <tileCacheConfig class="com.supermap.services.tilesource.UGCV5TileSourceInfo">
      <datastoreType>TILES</datastoreType>
      <type>UGCV5</type>
      <outputPath>./output/cache</outputPath>
      <storageType>Original</storageType>
    </tileCacheConfig>
    <useUTFGridCache>false</useUTFGridCache>
    <useVectorTileCache>false</useVectorTileCache>
    <cacheResamplingDisabled>false</cacheResamplingDisabled>
    <expired>0</expired>
    <cacheReadOnly>false</cacheReadOnly>
  </config>
</component>
<component alias="$DataServiceName" class="com.supermap.services.components.impl.DataImpl" enabled="true" initOnCreate="false" initPriority="0" instanceCount="0" interfaceNames="rest" name="$DataServiceName" providers="$DataServiceName">
  <config class="com.supermap.services.components.DataConfig">
    <editable>false</editable>
    <disableQueryCache>false</disableQueryCache>
  </config>
</component>

<!-- low_altitude_demo map/data service providers -->
<provider class="com.supermap.services.providers.UGCMapProvider" enabled="true" name="$MapServiceName">
  <config class="com.supermap.services.providers.UGCMapProviderSetting">
    <cacheVersion>5.0</cacheVersion>
    <workspacePath>$WorkspacePathInIServer</workspacePath>
    <layerCountPerDataType>0</layerCountPerDataType>
    <multiThread>true</multiThread>
    <poolSize>0</poolSize>
    <ugcMapSettings/>
    <useCompactCache>false</useCompactCache>
    <extractCacheToFile>true</extractCacheToFile>
    <queryExpectCount>1000</queryExpectCount>
    <ignoreHashcodeWhenUseCache>false</ignoreHashcodeWhenUseCache>
    <isMultiInstance>false</isMultiInstance>
    <inflatDisabled>false</inflatDisabled>
    <mapEditable>false</mapEditable>
    <dpi>96.0</dpi>
    <fullLabelEnabled>false</fullLabelEnabled>
    <cacheDisabled>false</cacheDisabled>
    <tileCacheReadOnly>false</tileCacheReadOnly>
    <vectorTileCacheDisabled>false</vectorTileCacheDisabled>
    <vectorTileCacheReadOnly>false</vectorTileCacheReadOnly>
    <usePreGeneratedUGCV5Cache>false</usePreGeneratedUGCV5Cache>
    <throwExceptionWhenOutputMapError>true</throwExceptionWhenOutputMapError>
  </config>
</provider>
<provider class="com.supermap.services.providers.UGCDataProvider" enabled="true" name="$DataServiceName">
  <config class="com.supermap.services.providers.UGCDataProviderSetting">
    <maxFeatures>1000</maxFeatures>
    <workspacePath>$WorkspacePathInIServer</workspacePath>
    <datasourceInfos/>
    <datasourceNames/>
    <attachmentsEnabled>true</attachmentsEnabled>
    <featureMetadatasEnabled>false</featureMetadatasEnabled>
    <isMultiInstance>false</isMultiInstance>
    <isDatasetsCheck>false</isDatasetsCheck>
    <disableFieldNameToUpperCase>false</disableFieldNameToUpperCase>
    <dataProviderDelayCommitSetting>
      <enabled>false</enabled>
      <commitMode>INTERVALUPDATE</commitMode>
      <countToCommit>1000</countToCommit>
      <updateInterval>3600</updateInterval>
      <hour>3</hour>
      <minute>0</minute>
      <dayOfWeek>1,2,3,4,5,6,7</dayOfWeek>
      <logEntireErrorMsg>false</logEntireErrorMsg>
    </dataProviderDelayCommitSetting>
    <maxFeatureWriteThreadCount>1</maxFeatureWriteThreadCount>
    <writePermitTimeout>120</writePermitTimeout>
    <ignoreTotalCount>false</ignoreTotalCount>
  </config>
</provider>
"@

$sceneFragment = @"
<!-- Candidate only: project-owned 3D service. Not verified until a real scene exists in the workspace and REST /realspace/scenes.json passes. -->
<component alias="$SceneServiceName" class="com.supermap.services.components.impl.RealspaceImpl" enabled="true" initOnCreate="false" initPriority="0" instanceCount="0" interfaceNames="rest" name="$SceneServiceName" providers="$SceneServiceName">
  <config class="com.supermap.services.components.RealspaceConfig"/>
</component>
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

$fullDraft = @"
<?xml version="1.0" encoding="UTF-8"?>
<!-- Draft only. Do not copy over iServer WEB-INF/iserver-services.xml directly. Merge through iServer admin tools or a reviewed deployment script. -->
<application>
  <componentSets>
    <!-- Add component references if the target iServer deployment requires componentSet registration. -->
  </componentSets>
  <providerSets>
  </providerSets>
  <components>
$($mapDataFragment -split '<!-- low_altitude_demo map/data service providers -->' | Select-Object -First 1)
$(
if ($IncludeUnverified3D) {
  $sceneFragment -split '<provider class=' | Select-Object -First 1
}
)
  </components>
  <providers>
$($mapDataFragment -split '<!-- low_altitude_demo map/data service providers -->' | Select-Object -Last 1)
$(
if ($IncludeUnverified3D) {
  '<provider class=' + (($sceneFragment -split '<provider class=' | Select-Object -Last 1))
}
)
  </providers>
</application>
"@

Set-Content -LiteralPath $mapDataFragmentPath -Value $mapDataFragment -Encoding UTF8
Set-Content -LiteralPath $fullDraftPath -Value $fullDraft -Encoding UTF8
if ($IncludeUnverified3D) {
  Set-Content -LiteralPath $sceneFragmentPath -Value $sceneFragment -Encoding UTF8
}

[xml]$null = Get-Content -LiteralPath $fullDraftPath -Raw -Encoding UTF8

$summary = [ordered]@{
  generated_at = (Get-Date).ToString("s")
  map_service = $MapServiceName
  data_service = $DataServiceName
  scene_service_candidate = $SceneServiceName
  workspace_path_in_iserver = $WorkspacePathInIServer
  map_data_fragment = $mapDataFragmentPath
  full_draft = $fullDraftPath
  unverified_3d_fragment = if ($IncludeUnverified3D) { $sceneFragmentPath } else { $null }
  strict_status = "map/data XML route documented; 3D service remains unverified until a real scene REST gate passes"
}

$summary | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $summaryPath -Encoding UTF8

Write-Host "[OK] map/data iServer config fragment => $mapDataFragmentPath"
Write-Host "[OK] full draft XML is well formed => $fullDraftPath"
if ($IncludeUnverified3D) {
  Write-Host "[WARN] unverified 3D candidate fragment generated => $sceneFragmentPath"
}
Write-Host "[OK] summary => $summaryPath"

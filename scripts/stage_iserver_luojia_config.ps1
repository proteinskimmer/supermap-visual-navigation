param(
  [string]$InstallRoot = "E:\supermap_software\supermap-iserver-2025u1a-windows-x64-all",
  [string]$ProjectRoot = "E:\supermap_project",
  [string]$WorkspacePathInIServer = '${fileManagerWorkDir}/luojia_workspace/luojia_mountain_demo.smwu',
  [string]$MapServiceName = "map-luojia_mountain_demo",
  [string]$DataServiceName = "data-luojia_mountain_demo",
  [string]$SceneServiceName = "3D-luojia_mountain_demo",
  [string]$OutputDir = "docs\supermap_integration\generated"
)

$ErrorActionPreference = "Stop"

$sourceXml = Join-Path $InstallRoot "webapps\iserver\WEB-INF\iserver-services.xml"
if (-not (Test-Path -LiteralPath $sourceXml)) {
  throw "iServer services XML not found: $sourceXml"
}

$outputRoot = Join-Path $ProjectRoot $OutputDir
New-Item -ItemType Directory -Force -Path $outputRoot | Out-Null

$stagedXml = Join-Path $outputRoot "iserver-services.with-luojia_mountain_demo.staged.xml"
$summaryPath = Join-Path $outputRoot "iserver_luojia_stage_summary.json"

$componentBlock = @"
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
    <component alias="$SceneServiceName" class="com.supermap.services.components.impl.RealspaceImpl" enabled="true" initOnCreate="false" initPriority="0" instanceCount="0" interfaceNames="rest" name="$SceneServiceName" providers="$SceneServiceName">
      <config class="com.supermap.services.components.RealspaceConfig"/>
    </component>
"@

$providerBlock = @"
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

$serviceNames = @($MapServiceName, $DataServiceName, $SceneServiceName)
$staged = Get-Content -LiteralPath $sourceXml -Raw -Encoding UTF8
foreach ($name in $serviceNames) {
  $escaped = [regex]::Escape($name)
  $componentPattern = "(?s)\s*<component\b[^>]*(?:alias|name)=`"$escaped`"[^>]*>.*?</component>"
  $providerPattern = "(?s)\s*<provider\b[^>]*name=`"$escaped`"[^>]*>.*?</provider>"
  $staged = [regex]::Replace($staged, $componentPattern, "")
  $staged = [regex]::Replace($staged, $providerPattern, "")
}

$staged = $staged -replace '(?s)(\s*</components>)', "`r`n$componentBlock`r`n`$1"
$staged = $staged -replace '(?s)(\s*</providers>)', "`r`n$providerBlock`r`n`$1"

Set-Content -LiteralPath $stagedXml -Value $staged -Encoding UTF8
[xml]$null = Get-Content -LiteralPath $stagedXml -Raw -Encoding UTF8

$summary = [ordered]@{
  generated_at = (Get-Date).ToString("s")
  source_xml = $sourceXml
  staged_xml = $stagedXml
  workspace_path_in_iserver = $WorkspacePathInIServer
  map_service = $MapServiceName
  data_service = $DataServiceName
  scene_service = $SceneServiceName
  strict_status = "staged only; not applied to iServer until apply script runs"
}

$summary | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $summaryPath -Encoding UTF8

Write-Host "[OK] staged iServer Luojia config XML => $stagedXml"
Write-Host "[OK] staged XML is well formed"
Write-Host "[OK] summary => $summaryPath"

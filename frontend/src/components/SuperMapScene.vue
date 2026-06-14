<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, shallowRef, watch } from "vue";
import MockMissionMap from "./MockMissionMap.vue";
import {
  createViewer,
  destroyViewer,
  detectWebGL2,
  drawDemoOverlay,
  fitToLargeArea,
  fitToTask,
  getSuperMapDebugState,
  installGentleWheelZoom,
  installMapImageryFallback,
  isLuojiaSuperMapConfig,
  loadSuperMap3D,
  openScene,
  syncSceneLayerVisibility,
  updateCurrentPoint,
  updateVisionCandidates,
} from "../services/supermap3d";

const props = defineProps({
  taskDetail: { type: Object, required: true },
  selectedTask: { type: Object, required: true },
  layers: { type: Array, default: () => [] },
  routes: { type: Array, default: () => [] },
  selectedRoute: { type: Object, default: null },
  riskAnalysis: { type: Object, default: null },
  temporaryRisk: { type: Object, default: null },
  replannedRoute: { type: Object, default: null },
  visionResult: { type: Object, default: null },
  visionTiles: { type: Array, default: () => [] },
  currentPoint: { type: Array, default: null },
  actualFlightTrail: { type: Array, default: () => [] },
  referenceFlightTrail: { type: Array, default: () => [] },
  visualMatchPoints: { type: Array, default: () => [] },
  supermapConfig: { type: Object, default: null },
});

const sceneProvider = import.meta.env.VITE_SCENE_PROVIDER || "auto";
const sdkBase = import.meta.env.VITE_SUPERMAP_SDK_BASE || "/vendor/supermap3d/Build/SuperMap3D";
const contextType = Number(import.meta.env.VITE_SUPERMAP_CONTEXT_TYPE || 2);
const mountEl = shallowRef(null);
const viewerRef = shallowRef(null);
const sdkRef = shallowRef(null);
const status = shallowRef("mock");
const error = shallowRef("");
const sceneWarning = shallowRef("");
const hasWebGL2 = shallowRef(false);
const debugState = shallowRef(null);
const luojiaBuildings = shallowRef([]);
const luojiaTerrain = shallowRef(null);
const viewScope = shallowRef("task");
let cameraFitted = false;
let wheelZoomCleanup = null;

const sceneServices = computed(() =>
  props.layers
    .filter((layer) => layer.service_url)
    .map((layer) => ({
      id: layer.id,
      name: layer.name,
      type: layer.type,
      url: layer.service_url,
    }))
);

const sceneUrl = computed(() => {
  return (
    import.meta.env.VITE_SUPERMAP_SCENE_URL ||
    props.supermapConfig?.services?.scene?.url ||
    sceneServices.value.find((service) => service.type === "3d")?.url ||
    ""
  );
});

const isSuperMapMode = computed(() => sceneProvider === "supermap" || (sceneProvider === "auto" && Boolean(sceneUrl.value)));
const isLuojiaMode = computed(() => isLuojiaSuperMapConfig(props.supermapConfig));

const statusText = computed(() => {
  if (!isSuperMapMode.value) return "二维态势备用图";
  if (error.value) return `SuperMap 已回退：${error.value}`;
  if (status.value === "loading-sdk") return "正在加载 SuperMap3D SDK";
  if (status.value === "creating-viewer") return "正在创建 SuperMap3D 视图";
  if (status.value === "opening-scene") return "正在打开 iServer 三维场景";
  if (status.value === "ready" && sceneWarning.value) return `SuperMap 本地仿真底座已就绪：${sceneWarning.value}`;
  if (status.value === "ready") return sceneUrl.value ? "SuperMap 场景已就绪" : "SuperMap 空三维球已就绪";
  return "等待 SuperMap 初始化";
});

const overlayData = computed(() => ({
  taskDetail: props.taskDetail,
  selectedTask: props.selectedTask,
  routes: props.routes,
  selectedRoute: props.selectedRoute,
  temporaryRisk: props.temporaryRisk,
  replannedRoute: props.replannedRoute,
  visionTiles: props.visionTiles,
  luojiaBuildings: luojiaBuildings.value,
  luojiaTerrain: luojiaTerrain.value,
  layers: props.layers,
  supermapConfig: props.supermapConfig,
  sceneUrl: sceneUrl.value,
}));

onMounted(() => {
  loadLuojiaBuildings();
  loadLuojiaTerrain();
  if (isSuperMapMode.value) {
    initializeSuperMap();
  }
});

watch(isSuperMapMode, async (enabled) => {
  if (enabled && !viewerRef.value && !["loading-sdk", "creating-viewer", "opening-scene"].includes(status.value)) {
    await nextTick();
    initializeSuperMap();
  }
});

watch(
  overlayData,
  () => {
    if (viewerRef.value && sdkRef.value && status.value === "ready") {
      refreshSceneBase();
    }
  },
  { deep: true }
);

watch(
  () => props.visionResult?.candidates || [],
  (candidates) => {
    if (viewerRef.value && sdkRef.value && status.value === "ready") {
      updateVisionCandidates(viewerRef.value, sdkRef.value, candidates);
      refreshDebugState();
    }
  },
  { deep: true }
);

watch(
  () => [props.currentPoint, props.actualFlightTrail, props.referenceFlightTrail, props.visualMatchPoints],
  ([point, actualTrail, referenceTrail, visualMatchPoints]) => {
    if (viewerRef.value && sdkRef.value && status.value === "ready") {
      updateCurrentPoint(viewerRef.value, sdkRef.value, point, {
        actualTrail,
        referenceTrail,
        visualMatchPoints,
      });
      refreshDebugState();
    }
  },
  { deep: true }
);

onBeforeUnmount(() => {
  cleanupWheelZoom();
  destroyViewer(viewerRef.value);
  viewerRef.value = null;
  sdkRef.value = null;
});

async function initializeSuperMap() {
  try {
    await nextTick();
    if (!mountEl.value) return;
    error.value = "";
    sceneWarning.value = "";
    hasWebGL2.value = detectWebGL2();
    if (!hasWebGL2.value && contextType === 2) {
      throw new Error("当前浏览器不支持 WebGL2");
    }

    status.value = "loading-sdk";
    const SuperMap3D = await loadSuperMap3D({ sdkBase });
    sdkRef.value = SuperMap3D;

    status.value = "creating-viewer";
    const viewer = createViewer(mountEl.value, SuperMap3D, { contextType });
    viewerRef.value = viewer;
    window.__supermapViewer = viewer;
    wheelZoomCleanup = installGentleWheelZoom(mountEl.value, viewer);

    status.value = "ready";
    refreshSceneBase();
    if (!cameraFitted) {
      fitToTask(viewer, SuperMap3D, props.selectedTask, props.supermapConfig);
      cameraFitted = true;
    }
    if (sceneUrl.value) {
      await tryOpenRemoteScene(viewer, SuperMap3D);
    }
  } catch (err) {
    error.value = err?.message || "SuperMap 初始化失败";
    status.value = "fallback";
    cleanupWheelZoom();
    destroyViewer(viewerRef.value);
    viewerRef.value = null;
    sdkRef.value = null;
    refreshDebugState();
  }
}

async function tryOpenRemoteScene(viewer, SuperMap3D) {
  sceneWarning.value = "正在连接 iServer，备用底座保持可用";
  try {
    await withTimeout(openScene(viewer, sceneUrl.value), 7000, "iServer scene open timeout");
    sceneWarning.value = "";
  } catch (err) {
    sceneWarning.value = "iServer 未就绪，使用本地 DEM/正射影像/建筑底座";
    console.warn("SuperMap remote scene unavailable; local Luojia base remains active", err);
  } finally {
    refreshSceneBase();
    fitToTask(viewer, SuperMap3D, props.selectedTask, props.supermapConfig);
  }
}

function withTimeout(promise, timeoutMs, message) {
  let timer = null;
  const timeout = new Promise((_, reject) => {
    timer = window.setTimeout(() => reject(new Error(message)), timeoutMs);
  });
  return Promise.race([promise, timeout]).finally(() => {
    window.clearTimeout(timer);
  });
}

async function loadLuojiaBuildings() {
  try {
    const response = await fetch("/demo/luojia_buildings_preview.json");
    if (!response.ok) return;
    const payload = await response.json();
    luojiaBuildings.value = payload.buildings || [];
  } catch (err) {
    console.warn("Failed to load Luojia buildings", err);
  }
}

async function loadLuojiaTerrain() {
  try {
    const response = await fetch("/demo/luojia_terrain_preview.json");
    if (!response.ok) return;
    luojiaTerrain.value = await response.json();
  } catch (err) {
    console.warn("Failed to load Luojia terrain", err);
  }
}

function refreshSceneBase() {
  if (!viewerRef.value || !sdkRef.value || status.value !== "ready") return;
  installMapImageryFallback(viewerRef.value, sdkRef.value, props.supermapConfig);
  syncSceneLayerVisibility(viewerRef.value, props.layers, props.supermapConfig);
  drawDemoOverlay(viewerRef.value, sdkRef.value, {
    ...overlayData.value,
    visionResult: props.visionResult,
  });
  updateCurrentPoint(viewerRef.value, sdkRef.value, props.currentPoint, {
    actualTrail: props.actualFlightTrail,
    referenceTrail: props.referenceFlightTrail,
    visualMatchPoints: props.visualMatchPoints,
  });
  refreshDebugState();
}

function cleanupWheelZoom() {
  wheelZoomCleanup?.();
  wheelZoomCleanup = null;
}

function resetStandardView() {
  if (!viewerRef.value || !sdkRef.value || status.value !== "ready") return;
  viewScope.value = "task";
  fitToTask(viewerRef.value, sdkRef.value, props.selectedTask, props.supermapConfig);
  refreshDebugState();
}

function showLargeAreaView() {
  if (!viewerRef.value || !sdkRef.value || status.value !== "ready") return;
  viewScope.value = "regional";
  fitToLargeArea(viewerRef.value, sdkRef.value, props.supermapConfig);
  refreshDebugState();
}

function reloadSceneBase() {
  refreshSceneBase();
  resetStandardView();
}

function refreshDebugState() {
  if (!viewerRef.value) {
    debugState.value = null;
    return;
  }
  debugState.value = getSuperMapDebugState(viewerRef.value, props.supermapConfig);
}
</script>

<template>
  <div class="scene-shell">
    <div v-if="isSuperMapMode" class="supermap-scene">
      <div
        ref="mountEl"
        :class="['supermap-mount', isLuojiaMode ? 'luojia-base-mount' : '']"
        data-supermap-mount
        :data-scene-status="status"
        :data-view-scope="viewScope"
        :data-luojia-mode="isLuojiaMode ? 'true' : 'false'"
        :data-regional-terrain-installed="debugState?.regionalTerrainInstalled ? 'true' : 'false'"
        :data-online-basemap-status="debugState?.onlineBasemapStatus || 'not_configured'"
        :data-online-terrain-status="debugState?.onlineTerrainStatus || 'not_configured'"
        :data-luojia-fallback-installed="debugState?.fallbackInstalled ? 'true' : 'false'"
        :data-luojia-terrain-installed="debugState?.terrainInstalled ? 'true' : 'false'"
      ></div>
      <div class="scene-control-bar">
        <button
          type="button"
          title="飞到珞珈山周边大范围三维场景"
          data-regional-3d-view-button
          :disabled="status !== 'ready'"
          @click="showLargeAreaView"
        >
          区域三维
        </button>
        <button type="button" title="重新加载珞珈底图" :disabled="status !== 'ready'" @click="reloadSceneBase">
          重载底图
        </button>
        <button type="button" title="飞回任务标准视角" :disabled="status !== 'ready'" @click="resetStandardView">
          标准视角
        </button>
      </div>
      <details class="supermap-empty-state supermap-status-panel">
        <summary>
          <strong>场景状态</strong>
          <span>{{ statusText }}</span>
        </summary>
        <div class="supermap-status-detail">
        <small>SDK 路径：{{ sdkBase }}</small>
        <small>WebGL2：{{ hasWebGL2 ? "可用" : "未确认" }} / 上下文类型：{{ contextType }}</small>
        <small v-if="sceneUrl">场景地址：{{ sceneUrl }}</small>
        <small v-if="debugState">
          珞珈备用底图：{{ debugState.fallbackInstalled ? "已安装" : "未安装" }} /
          场景图层：{{ debugState.sceneLayerCount }} /
          影像图层：{{ debugState.imageryLayerCount }}
        </small>
        <small v-if="debugState">
          在线底图：{{ debugState.onlineBasemapStatus }} / 在线地形：{{ debugState.onlineTerrainStatus }}
        </small>
        <small v-if="debugState?.onlineRegionalImageryInstalled">
          在线区域影像瓦片：{{ debugState.onlineRegionalImageryTiles }} 张 / z{{ debugState.onlineRegionalImageryZoom }}
        </small>
        <small v-if="debugState?.terrainInstalled">
          高程地形网格：{{ debugState.terrainVertices }} 个顶点 / {{ debugState.terrainTriangles }} 个三角面
        </small>
        <small v-if="debugState?.regionalTerrainInstalled">
          区域三维底座：{{ debugState.regionalTerrainVertices }} 个顶点 / {{ debugState.regionalTerrainTriangles }} 个三角面
        </small>
        <small v-if="sceneWarning">{{ sceneWarning }}</small>
        <small v-if="isLuojiaMode">正射影像备用图：/demo/luojia_ortho_preview.jpg</small>
        <small v-if="isLuojiaMode">图例：灰色=建筑 / 橙红=风险 / 青色=视觉匹配区</small>
        <small v-if="!sceneUrl">未配置场景地址，当前在 SuperMap 空三维球上绘制任务叠加层。</small>
        </div>
      </details>

      <MockMissionMap
        v-if="error"
        class="supermap-fallback-map"
        :task-detail="taskDetail"
        :selected-task="selectedTask"
        :layers="layers"
        :routes="routes"
        :selected-route="selectedRoute"
        :risk-analysis="riskAnalysis"
        :temporary-risk="temporaryRisk"
        :replanned-route="replannedRoute"
        :vision-result="visionResult"
        :vision-tiles="visionTiles"
        :current-point="currentPoint"
        :actual-flight-trail="actualFlightTrail"
        :reference-flight-trail="referenceFlightTrail"
        :visual-match-points="visualMatchPoints"
      />
    </div>

    <MockMissionMap
      v-else
      :task-detail="taskDetail"
      :selected-task="selectedTask"
      :layers="layers"
      :routes="routes"
      :selected-route="selectedRoute"
      :risk-analysis="riskAnalysis"
      :temporary-risk="temporaryRisk"
      :replanned-route="replannedRoute"
      :vision-result="visionResult"
      :vision-tiles="visionTiles"
      :current-point="currentPoint"
      :actual-flight-trail="actualFlightTrail"
      :reference-flight-trail="referenceFlightTrail"
      :visual-match-points="visualMatchPoints"
    />
  </div>
</template>

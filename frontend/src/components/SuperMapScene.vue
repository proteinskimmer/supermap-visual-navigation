<script setup>
import { computed, onBeforeUnmount, onMounted, shallowRef, watch } from "vue";
import MockMissionMap from "./MockMissionMap.vue";
import {
  createViewer,
  destroyViewer,
  detectWebGL2,
  drawDemoOverlay,
  fitToTask,
  loadSuperMap3D,
  openScene,
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
  supermapConfig: { type: Object, default: null },
});

const sceneProvider = import.meta.env.VITE_SCENE_PROVIDER || "mock";
const sdkBase = import.meta.env.VITE_SUPERMAP_SDK_BASE || "/vendor/supermap3d/Build/SuperMap3D";
const contextType = Number(import.meta.env.VITE_SUPERMAP_CONTEXT_TYPE || 2);
const mountEl = shallowRef(null);
const viewerRef = shallowRef(null);
const sdkRef = shallowRef(null);
const status = shallowRef("mock");
const error = shallowRef("");
const hasWebGL2 = shallowRef(false);
let cameraFitted = false;

const isSuperMapMode = computed(() => sceneProvider === "supermap");

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

const mapService = computed(() => props.supermapConfig?.services?.map || null);
const dataService = computed(() => props.supermapConfig?.services?.data || null);
const mapResourceUrl = computed(() => mapService.value?.resource_url || mapService.value?.url || "");

const statusText = computed(() => {
  if (!isSuperMapMode.value) return "mock SVG 态势图";
  if (error.value) return `SuperMap 回退：${error.value}`;
  if (status.value === "loading-sdk") return "加载 SuperMap3D SDK";
  if (status.value === "creating-viewer") return "创建 SuperMap3D Viewer";
  if (status.value === "opening-scene") return "打开 iServer 三维场景";
  if (status.value === "ready") return sceneUrl.value ? "SuperMap 场景已就绪" : "SuperMap 空球已就绪";
  return "等待 SuperMap 初始化";
});

const overlayData = computed(() => ({
  taskDetail: props.taskDetail,
  selectedTask: props.selectedTask,
  routes: props.routes,
  selectedRoute: props.selectedRoute,
  temporaryRisk: props.temporaryRisk,
  replannedRoute: props.replannedRoute,
  visionResult: props.visionResult,
  visionTiles: props.visionTiles,
  currentPoint: props.currentPoint,
}));

onMounted(() => {
  if (isSuperMapMode.value) {
    initializeSuperMap();
  }
});

onBeforeUnmount(() => {
  destroyViewer(viewerRef.value);
  viewerRef.value = null;
  sdkRef.value = null;
});

watch(
  overlayData,
  () => {
    if (viewerRef.value && sdkRef.value && status.value === "ready") {
      drawDemoOverlay(viewerRef.value, sdkRef.value, overlayData.value);
    }
  },
  { deep: true }
);

async function initializeSuperMap() {
  try {
    error.value = "";
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

    if (sceneUrl.value) {
      status.value = "opening-scene";
      await openScene(viewer, sceneUrl.value);
    }

    status.value = "ready";
    drawDemoOverlay(viewer, SuperMap3D, overlayData.value);
    if (!cameraFitted) {
      fitToTask(viewer, SuperMap3D, props.selectedTask);
      cameraFitted = true;
    }
  } catch (err) {
    error.value = err?.message || "SuperMap 初始化失败";
    status.value = "fallback";
    destroyViewer(viewerRef.value);
    viewerRef.value = null;
  }
}
</script>

<template>
  <div class="scene-shell">
    <div v-if="isSuperMapMode" class="supermap-scene">
      <div ref="mountEl" class="supermap-mount" data-supermap-mount></div>
      <div class="supermap-empty-state">
        <strong>SuperMap iClient3D</strong>
        <span>{{ statusText }}</span>
        <small>SDK: {{ sdkBase }}</small>
        <small>WebGL2: {{ hasWebGL2 ? "可用" : "未确认/不可用" }} · contextType: {{ contextType }}</small>
        <small v-if="sceneUrl">scene.open(sceneUrl): {{ sceneUrl }}</small>
        <small v-else>未配置 sceneUrl，当前只在空三维球上绘制 mock 航线和业务图形。</small>
      </div>

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
    />
  </div>
</template>

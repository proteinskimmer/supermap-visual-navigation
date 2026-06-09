<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import EmptyState from "./components/EmptyState.vue";
import InspectorPanel from "./components/InspectorPanel.vue";
import ReportPage from "./components/ReportPage.vue";
import SuperMapScene from "./components/SuperMapScene.vue";
import TaskSidebar from "./components/TaskSidebar.vue";
import TimelinePanel from "./components/TimelinePanel.vue";
import { api } from "./services/api";

const tasks = ref([]);
const taskDetail = ref(null);
const layers = ref([]);
const routes = ref([]);
const selectedRoute = ref(null);
const riskAnalysis = ref(null);
const simulation = ref(null);
const temporaryRisk = ref(null);
const replannedRoute = ref(null);
const visionResult = ref(null);
const visionImages = ref([]);
const visionTiles = ref([]);
const selectedVisionImageId = ref("demo_uav_001");
const visionTopK = ref(3);
const supermapConfig = ref(null);
const supermapStatus = ref(null);
const supermapRefreshing = ref(false);
const reportResult = ref(null);
const loading = ref("初始化");
const actionError = ref("");
const fatalError = ref("");
const simProgress = ref(0);
const playTimer = ref(null);
const activeView = ref("workspace");

const isBusy = computed(() => Boolean(loading.value));
const selectedTask = computed(() => taskDetail.value?.task);
const currentRouteForDisplay = computed(() => replannedRoute.value?.route || selectedRoute.value);
const selectedVisionImage = computed(() =>
  visionImages.value.find((image) => image.id === selectedVisionImageId.value)
);
const bestVisionCandidate = computed(() =>
  visionResult.value?.candidates?.find((candidate) => candidate.status === "best")
);

const events = computed(() => {
  const base = simulation.value?.events || [];
  const extra = [];
  if (temporaryRisk.value?.event) extra.push(temporaryRisk.value.event);
  if (replannedRoute.value?.event) extra.push(replannedRoute.value.event);
  if (visionResult.value && bestVisionCandidate.value) {
    const confidence = Math.round(bestVisionCandidate.value.confidence * 100);
    extra.push({
      time_s: selectedVisionImage.value?.capture_time_s || 0,
      type: "vision_match",
      title: bestVisionCandidate.value.confidence < 0.5 ? "视觉匹配需要复核" : "视觉匹配完成",
      description: `最优候选 ${bestVisionCandidate.value.tile_id}，置信度 ${confidence}%，匹配点 ${bestVisionCandidate.value.matched_points}。`,
      position: bestVisionCandidate.value.center,
    });
  }
  return [...base, ...extra].sort((a, b) => a.time_s - b.time_s);
});

const currentPoint = computed(() => {
  const route = currentRouteForDisplay.value;
  if (!route?.points?.length) return null;
  const index = Math.min(route.points.length - 1, Math.floor((simProgress.value / 100) * (route.points.length - 1)));
  return route.points[index];
});

const demoStage = computed(() => {
  if (reportResult.value) return "报告已生成";
  if (replannedRoute.value) return "已完成动态重规划";
  if (temporaryRisk.value) return "临时风险区已触发";
  if (simulation.value) return "仿真进行中";
  if (routes.value.length) return "候选航线已生成";
  return "等待任务加载";
});

const canTriggerReplan = computed(() => Boolean(simulation.value && selectedRoute.value && !replannedRoute.value));

const demoSteps = computed(() => [
  { label: "任务和图层加载", done: Boolean(selectedTask.value && layers.value.length) },
  { label: "三条候选航线", done: routes.value.length >= 3 },
  { label: "风险评分和剖面", done: Boolean(riskAnalysis.value) },
  { label: "仿真时间轴", done: Boolean(simulation.value) },
  { label: "临时风险区", done: Boolean(temporaryRisk.value) },
  { label: "动态重规划", done: Boolean(replannedRoute.value) },
  { label: "视觉候选区域", done: Boolean(visionResult.value?.candidates?.length) },
  { label: "任务报告", done: Boolean(reportResult.value) },
]);

function messageFromError(err) {
  return err?.message || "操作失败，请检查后端接口或本地环境。";
}

async function runAction(label, fn) {
  try {
    actionError.value = "";
    loading.value = label;
    return await fn();
  } catch (err) {
    actionError.value = `${label}失败：${messageFromError(err)}`;
    return null;
  } finally {
    loading.value = "";
  }
}

async function initialize() {
  try {
    fatalError.value = "";
    loading.value = "加载任务";
    tasks.value = await api.tasks();
    if (!tasks.value.length) {
      fatalError.value = "后端未返回任务列表。";
      return;
    }
    const taskId = tasks.value[0].id;
    const [detail, layerList, supermap, supermapRuntime] = await Promise.all([
      api.taskDetail(taskId),
      api.layers(),
      api.supermapConfig().catch(() => null),
      api.supermapStatus().catch(() => null),
    ]);
    taskDetail.value = detail;
    layers.value = layerList;
    supermapConfig.value = supermap;
    supermapStatus.value = supermapRuntime;
    await loadVisionFrameworkData(taskId);
    await planRoutes();
    await runVisionMatch();
  } catch (err) {
    fatalError.value = `后端暂不可用：${messageFromError(err)}`;
  } finally {
    loading.value = "";
  }
}

async function loadVisionFrameworkData(taskId) {
  const [images, tiles] = await Promise.all([api.visionImages(taskId), api.visionTiles(taskId)]);
  visionImages.value = images;
  visionTiles.value = tiles;
  selectedVisionImageId.value = images[0]?.id || "demo_uav_001";
}

async function planRoutes() {
  if (!selectedTask.value) {
    actionError.value = "任务尚未加载，无法规划航线。";
    return;
  }
  await runAction("规划航线", async () => {
    resetSimulation();
    reportResult.value = null;
    const planned = await api.planRoutes({
      task_id: selectedTask.value.id,
      start: selectedTask.value.start,
      target: selectedTask.value.target,
      modes: ["shortest", "safest", "balanced"],
    });
    routes.value = planned;
    selectedRoute.value = planned.find((route) => route.mode === "balanced") || planned[0] || null;
    await analyzeSelectedRoute();
  });
}

async function analyzeSelectedRoute() {
  if (!selectedTask.value || !selectedRoute.value) return;
  riskAnalysis.value = await api.analyzeRisk({
    task_id: selectedTask.value.id,
    route: selectedRoute.value,
  });
}

async function selectRoute(route) {
  await runAction("风险校验", async () => {
    selectedRoute.value = route;
    await analyzeSelectedRoute();
  });
}

async function startSimulation() {
  if (!selectedRoute.value) {
    actionError.value = "请先选择一条候选航线。";
    return;
  }
  await runAction("启动仿真", async () => {
    simulation.value = await api.startSimulation({
      task_id: selectedTask.value.id,
      route: selectedRoute.value,
    });
    simProgress.value = 0;
    temporaryRisk.value = null;
    replannedRoute.value = null;
  });
}

function advanceSimulation() {
  if (!simulation.value) {
    actionError.value = "仿真尚未启动。";
    return;
  }
  simProgress.value = Math.min(100, simProgress.value + 12);
}

async function toggleAutoPlay() {
  if (playTimer.value) {
    clearInterval(playTimer.value);
    playTimer.value = null;
    return;
  }
  if (!simulation.value) {
    await startSimulation();
    if (!simulation.value) return;
  }
  playTimer.value = setInterval(() => {
    simProgress.value = Math.min(100, simProgress.value + 2);
    if (simProgress.value >= 100 && playTimer.value) {
      clearInterval(playTimer.value);
      playTimer.value = null;
    }
  }, 350);
}

function resetSimulation() {
  if (playTimer.value) {
    clearInterval(playTimer.value);
    playTimer.value = null;
  }
  simProgress.value = 0;
  temporaryRisk.value = null;
  replannedRoute.value = null;
}

async function triggerTemporaryRisk() {
  if (!canTriggerReplan.value) {
    actionError.value = "请先启动仿真，再触发动态重规划。";
    return;
  }
  await runAction("动态重规划", async () => {
    const point = currentPoint.value || selectedRoute.value.points[Math.floor(selectedRoute.value.points.length / 2)];
    const timeS = Math.round((simProgress.value / 100) * selectedRoute.value.estimated_time_s);
    temporaryRisk.value = await api.temporaryRisk(simulation.value.simulation_id, {
      task_id: selectedTask.value.id,
      current_position: point,
      time_s: timeS,
    });
    replannedRoute.value = await api.replan({
      task_id: selectedTask.value.id,
      current_position: point,
      target: selectedTask.value.target,
      temporary_risks: [temporaryRisk.value.risk],
      time_s: timeS + 8,
    });
  });
}

async function runVisionMatch() {
  await runAction("视觉匹配", async () => {
    visionResult.value = await api.visionMatch({
      task_id: selectedTask.value?.id || "task_001",
      image_id: selectedVisionImageId.value,
      top_k: visionTopK.value,
      algorithm_mode: "precomputed",
    });
  });
}

async function selectVisionImage(imageId) {
  selectedVisionImageId.value = imageId;
  await runVisionMatch();
}

async function updateVisionTopK(topK) {
  visionTopK.value = topK;
  await runVisionMatch();
}

async function loadReport() {
  if (!selectedTask.value) {
    actionError.value = "任务尚未加载，无法生成报告。";
    return;
  }
  await runAction("生成报告", async () => {
    reportResult.value = await api.report(selectedTask.value.id);
    activeView.value = "report";
  });
}

async function refreshSuperMapStatus() {
  await runAction("检测 SuperMap 服务", async () => {
    supermapRefreshing.value = true;
    const [supermap, supermapRuntime] = await Promise.all([
      api.supermapConfig().catch(() => supermapConfig.value),
      api.supermapStatus(),
    ]);
    supermapConfig.value = supermap;
    supermapStatus.value = supermapRuntime;
  });
  supermapRefreshing.value = false;
}

onMounted(initialize);
onBeforeUnmount(() => {
  if (playTimer.value) clearInterval(playTimer.value);
});
</script>

<template>
  <ReportPage
    v-if="activeView === 'report'"
    :report="reportResult"
    :risk-analysis="riskAnalysis"
    :events="events"
    :loading="isBusy"
    :error="actionError"
    @close="activeView = 'workspace'"
    @reload="loadReport"
  />

  <main v-else class="app-shell">
    <header class="topbar">
      <div>
        <p class="eyebrow">SuperMap GIS Mock Workflow</p>
        <h1>低空视觉自主导航与三维仿真规划系统</h1>
      </div>
      <div class="status-cluster">
        <span :class="['status-dot', fatalError ? 'status-bad' : 'status-good']"></span>
        <span>{{ fatalError ? "接口未连接" : "接口已连接" }}</span>
      </div>
    </header>

    <section v-if="fatalError" class="banner">{{ fatalError }}</section>
    <section v-else-if="actionError" class="banner">{{ actionError }}</section>

    <section class="workspace">
      <TaskSidebar
        :tasks="tasks"
        :layers="layers"
        :supermap-config="supermapConfig"
        :supermap-status="supermapStatus"
        :supermap-refreshing="supermapRefreshing"
        :vision-images="visionImages"
        :selected-vision-image-id="selectedVisionImageId"
        :selected-task="selectedTask"
        :selected-route="selectedRoute"
        :simulation="simulation"
        :can-trigger-replan="canTriggerReplan"
        :is-playing="Boolean(playTimer)"
        :demo-steps="demoSteps"
        @plan-routes="planRoutes"
        @start-simulation="startSimulation"
        @advance-simulation="advanceSimulation"
        @toggle-play="toggleAutoPlay"
        @trigger-replan="triggerTemporaryRisk"
        @reset-simulation="resetSimulation"
        @open-report="loadReport"
        @select-vision-image="selectVisionImage"
        @refresh-supermap="refreshSuperMapStatus"
      />

      <section class="map-stage">
        <div class="map-toolbar">
          <strong>{{ selectedTask?.display_name || "任务区域" }}</strong>
          <span>{{ loading || demoStage }}</span>
        </div>

        <SuperMapScene
          v-if="taskDetail && selectedTask"
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
          :supermap-config="supermapConfig"
        />
        <EmptyState v-else title="任务区域未加载" message="等待后端任务详情和图层配置。" />
      </section>

      <InspectorPanel
        :routes="routes"
        :selected-route="selectedRoute"
        :risk-analysis="riskAnalysis"
        :vision-result="visionResult"
        :selected-vision-image="selectedVisionImage"
        :best-vision-candidate="bestVisionCandidate"
        :vision-tiles="visionTiles"
        :vision-top-k="visionTopK"
        @select-route="selectRoute"
        @update-vision-top-k="updateVisionTopK"
        @run-vision-match="runVisionMatch"
      />
    </section>

    <TimelinePanel :progress="simProgress" :events="events" />
  </main>
</template>

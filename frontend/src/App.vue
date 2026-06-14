<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import MissionEndpointEditor from "./components/MissionEndpointEditor.vue";
import ReportPage from "./components/ReportPage.vue";
import RiskZoneEditor from "./components/RiskZoneEditor.vue";
import SuperMapScene from "./components/SuperMapScene.vue";
import { api, API_ORIGIN } from "./services/api";

const SIM_PLAY_SECONDS = 18;

const tasks = ref([]);
const taskDetail = ref(null);
const layers = ref([]);
const routes = ref([]);
const selectedRoute = ref(null);
const riskAnalysis = ref(null);
const simulation = ref(null);
const navigationSession = ref(null);
const navigationState = ref(null);
const navigationTimeline = ref([]);
const temporaryRisk = ref(null);
const replannedRoute = ref(null);
const visionResult = ref(null);
const visualLocalization = ref(null);
const visionMatchCache = ref({});
const visualLocalizationCache = ref({});
const visionImages = ref([]);
const visionTiles = ref([]);
const selectedVisionImageId = ref("demo_uav_001");
const visionTopK = ref(3);
const lightingOptions = ref({
  capture_datetime: "2026-06-09T10:30",
  timezone_offset_hours: 8,
  exposure_ev: 0,
  shadow_strength: 0.22,
  haze: 0.08,
  color_temperature_k: 5600,
});
const supermapConfig = ref(null);
const supermapStatus = ref(null);
const reportResult = ref(null);
const reportLoading = ref(false);
const reportLoadingMessage = ref("");
const endpointEditDraft = ref(null);
const endpointSaveError = ref("");
const savingEndpoints = ref(false);
const riskEditDraft = ref(null);
const riskSaveError = ref("");
const savingRiskZones = ref(false);
const loading = ref("初始化");
const actionError = ref("");
const fatalError = ref("");
const simProgress = ref(0);
const playFrame = ref(null);
const activeView = ref("cockpit");
const activeCockpitSection = ref("situational");
const navigationMode = ref("autonomous");
const showShortestRoute = ref(false);
const simLogCollapsed = ref(false);
const isSimulationStarting = ref(false);
const preparingNavigation = ref(false);
const navigationPreparationMessage = ref("");
const preparedNavigationSession = ref(null);
const preparedNavigationKey = ref("");
let playLastTimestamp = 0;
let visionRequestToken = 0;
let navigationPreparationPromise = null;
let navigationPreparationKey = "";
let reportLoadingTimer = null;
const pendingVisionMatchRequests = new Map();
const pendingVisualLocalizationRequests = new Map();

const selectedTask = computed(() => taskDetail.value?.task || null);
const navigationMatcherMode = computed(() => "precomputed_proxy");
const taskDetailForDisplay = computed(() => {
  if (!taskDetail.value) return null;
  const task = endpointEditDraft.value
    ? {
        ...taskDetail.value.task,
        start: endpointEditDraft.value.start,
        target: endpointEditDraft.value.target,
      }
    : taskDetail.value.task;
  return {
    ...taskDetail.value,
    task,
    risk_zones: riskEditDraft.value || taskDetail.value.risk_zones || [],
  };
});
const currentRouteForDisplay = computed(() => replannedRoute.value?.route || selectedRoute.value);
const visibleSceneRoutes = computed(() =>
  routes.value.filter((route) => showShortestRoute.value || route.mode !== "shortest")
);
const isPlaying = computed(() => Boolean(playFrame.value));
const activeVisionImageId = computed(() => navigationState.value?.active_frame_id || selectedVisionImageId.value);
const selectedVisionImage = computed(() =>
  visionImages.value.find((image) => image.id === selectedVisionImageId.value) ||
  visionImages.value.find((image) => image.id === activeVisionImageId.value) ||
  null
);
const bestVisionCandidate = computed(() => {
  const fix = navigationState.value?.visual_position;
  if (fix) {
    return {
      tile_id: fix.tile_id,
      confidence: fix.confidence,
      matched_points: navigationState.value?.visual_frame?.matched_points || 0,
      inlier_ratio: navigationState.value?.visual_frame?.inlier_ratio || 0,
      center: poseToPoint(fix),
      status: navigationState.value?.navigation_mode === "review" ? "needs_review" : "best",
      reason: fix.reason,
    };
  }
  return visionResult.value?.candidates?.find((candidate) => candidate.status === "best") || null;
});
const bestSyntheticView = computed(() => {
  const bestMatch = visualLocalization.value?.matches?.[0];
  if (!bestMatch) return null;
  return visualLocalization.value.synthetic_views?.find((view) => view.view_id === bestMatch.view_id) || null;
});
const activeOrbEvidence = computed(() => visualLocalization.value?.matches?.[0]?.evidence?.urls || null);
const elapsedSeconds = computed(() => {
  if (navigationState.value) return navigationState.value.time_s;
  const total = navigationSession.value?.duration_s || currentRouteForDisplay.value?.estimated_time_s || 180;
  return Math.round((simProgress.value / 100) * total);
});

const referencePoint = computed(() => poseToPoint(navigationState.value?.reference_position));
const actualFlightTrail = computed(() => navigationTrail("fused_position"));
const referenceFlightTrail = computed(() => navigationTrail("reference_position"));
const visualMatchPoints = computed(() => {
  if (!navigationTimeline.value.length) return [];
  const seen = new Set();
  return navigationTimeline.value
    .filter((frame) => frame.time_s <= elapsedSeconds.value && frame.visual_position)
    .map((frame) => {
      const visual = frame.visual_position;
      const visualFrame = frame.visual_frame || {};
      return {
        id: visual.match_id || visual.image_id || `${frame.time_s}-${visual.tile_id}`,
        point: poseToPoint(frame.reference_position) || poseToPoint(visual),
        visualPoint: poseToPoint(visual),
        confidence: visual.confidence || 0,
        matchedPoints: visualFrame.matched_points || 0,
        inlierRatio: visualFrame.inlier_ratio || 0,
        timeS: frame.time_s,
        imageId: visual.image_id || frame.active_frame_id || "",
      };
    })
    .filter((match) => {
      if (!match.point || seen.has(match.id)) return false;
      seen.add(match.id);
      return true;
    });
});
const activeVisualControlPoint = computed(() => {
  if (!activeVisionImageId.value) return null;
  return visualMatchPoints.value.find((match) => match.imageId === activeVisionImageId.value) || null;
});
const sceneVisionResult = computed(() => {
  if (simulation.value && !activeVisualControlPoint.value) return null;
  return visionResult.value;
});

const visualNavigation = computed(() => {
  const state = navigationState.value;
  if (!state) {
    return {
      status: "waiting",
      label: "等待后端导航状态",
      confidence: 0,
      deviationM: 0,
      correction: [0, 0, 0],
      estimatedPoint: null,
      usedForNavigation: false,
      source: "reference_route",
    };
  }
  const confidence = state.visual_position?.confidence || 0;
  const labels = {
    autonomous: state.visual_position ? "后端视觉融合导航" : "参考航线导航",
    assisted: state.visual_position ? "后端视觉辅助定位" : "参考航线待视觉帧",
    review: "低置信复核模式",
  };
  return {
    status: state.navigation_mode,
    label: labels[state.navigation_mode],
    confidence,
    deviationM: state.deviation_m,
    correction: state.visual_position?.correction_vector_m || [0, 0, 0],
    estimatedPoint: poseToPoint(state.fused_position),
    referencePoint: poseToPoint(state.reference_position),
    visualPoint: poseToPoint(state.visual_position),
    usedForNavigation: state.telemetry.location_source === "visual_fusion",
    source: state.telemetry.location_source,
  };
});

const currentPoint = computed(() => poseToPoint(navigationState.value?.fused_position) || referencePoint.value);

const telemetry = computed(() => {
  const stateTelemetry = navigationState.value?.telemetry;
  const point = currentPoint.value || selectedTask.value?.start || [0, 0, 120];
  if (stateTelemetry) {
    return {
      uavId: stateTelemetry.uav_id,
      lon: point[0],
      lat: point[1],
      altitude: point[2] || 120,
      speed: stateTelemetry.speed_mps,
      heading: stateTelemetry.heading_deg,
      pitch: stateTelemetry.pitch_deg,
      roll: stateTelemetry.roll_deg,
      yaw: stateTelemetry.yaw_deg,
      battery: stateTelemetry.battery_pct,
      flightTime: stateTelemetry.flight_time,
      mode: replannedRoute.value ? "重规划跟踪" : visualNavigation.value.label,
    };
  }
  return {
    uavId: "UAV-011",
    lon: point[0],
    lat: point[1],
    altitude: point[2] || 120,
    speed: 0,
    heading: 0,
    pitch: -2,
    roll: 0,
    yaw: 0,
    battery: 96,
    flightTime: "00:00",
    mode: "任务待命",
  };
});

const events = computed(() => {
  const base = navigationSession.value?.events || simulation.value?.events || [];
  const extras = [];
  if (temporaryRisk.value?.event) extras.push(temporaryRisk.value.event);
  if (replannedRoute.value?.event) extras.push(replannedRoute.value.event);
  return [...base, ...extras].sort((a, b) => a.time_s - b.time_s);
});

const activeEvents = computed(() => events.value.filter((event) => event.time_s <= elapsedSeconds.value + 2).slice(-5).reverse());
const upcomingEvents = computed(() => events.value.filter((event) => event.time_s > elapsedSeconds.value).slice(0, 3));
const simulationLogs = computed(() => {
  if (!simulation.value) {
    return [];
  }
  const logs = [];
  if (navigationState.value) {
    logs.push({
      id: `state-${navigationState.value.time_s}`,
      time: navigationState.value.time_s,
      title: "导航状态更新",
      detail: `${locationSourceLabel(navigationState.value.telemetry?.location_source)} · 高度 ${telemetry.value.altitude.toFixed(1)} 米 · 速度 ${telemetry.value.speed.toFixed(1)} 米/秒`,
    });
  }
  activeEvents.value.forEach((event) => {
    logs.push({
      id: `event-${event.type}-${event.time_s}`,
      time: event.time_s,
      title: event.title || "任务事件",
      detail: event.description || "仿真事件已触发",
    });
  });
  if (visualNavigation.value.usedForNavigation) {
    logs.push({
      id: `vision-${navigationState.value?.time_s || 0}`,
      time: navigationState.value?.time_s || elapsedSeconds.value,
      title: "视觉融合生效",
      detail: `融合偏差 ${visualNavigation.value.deviationM} 米，置信度 ${confidencePercent(visualNavigation.value.confidence)}`,
    });
  }
  return logs.sort((a, b) => b.time - a.time).slice(0, 8);
});

const cockpitStatus = computed(() => {
  if (fatalError.value) return "接口异常";
  if (loading.value) return loading.value;
  if (replannedRoute.value) return "动态重规划完成";
  if (simulation.value) return navigationMode.value === "autonomous" ? "视觉自主导航中" : "视觉辅助导航中";
  if (routes.value.length) return "候选航线已生成";
  return "等待任务加载";
});

const routeSummary = computed(() => {
  const route = currentRouteForDisplay.value;
  if (!route) return { distance: "-", score: "-", risk: "-" };
  return {
    distance: `${route.distance_m} 米`,
    score: route.score,
    risk: route.risk_level,
  };
});

const canTriggerReplan = computed(() => Boolean(simulation.value && selectedRoute.value && !replannedRoute.value));

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

function navigationSessionKey(route = selectedRoute.value) {
  return [
    selectedTask.value?.id || "",
    route?.id || "",
    navigationMode.value,
    navigationMatcherMode.value,
  ].join("|");
}

function clearPreparedNavigation() {
  preparedNavigationSession.value = null;
  preparedNavigationKey.value = "";
  navigationPreparationMessage.value = "";
}

async function createNavigationSession(route = selectedRoute.value) {
  if (!selectedTask.value || !route) {
    throw new Error("缺少任务或航线，无法启动推演。");
  }
  const started = await api.startNavigation({
    task_id: selectedTask.value.id,
    route,
    mode: navigationMode.value,
    matcher_mode: navigationMatcherMode.value,
  });
  const session = started?.timeline?.length ? started : await api.navigationTimeline(started.session_id);
  if (!session?.timeline?.length) {
    throw new Error("后端未返回导航时间线。");
  }
  return session;
}

async function prepareNavigationSession({ silent = true } = {}) {
  const key = navigationSessionKey();
  if (!selectedTask.value || !selectedRoute.value) return null;
  if (preparedNavigationSession.value && preparedNavigationKey.value === key) {
    return preparedNavigationSession.value;
  }
  if (preparingNavigation.value && navigationPreparationKey === key && navigationPreparationPromise) {
    return navigationPreparationPromise;
  }

  navigationPreparationKey = key;
  preparingNavigation.value = true;
  navigationPreparationMessage.value = "正在预生成推演时间线...";
  navigationPreparationPromise = createNavigationSession(selectedRoute.value);

  try {
    const session = await navigationPreparationPromise;
    if (navigationPreparationKey === key) {
      preparedNavigationSession.value = session;
      preparedNavigationKey.value = key;
      navigationPreparationMessage.value = "推演时间线已准备";
    }
    return session;
  } catch (err) {
    if (navigationPreparationKey === key) {
      clearPreparedNavigation();
      navigationPreparationMessage.value = `推演预生成失败：${messageFromError(err)}`;
    }
    if (!silent) throw err;
    return null;
  } finally {
    if (navigationPreparationKey === key) {
      preparingNavigation.value = false;
      navigationPreparationPromise = null;
    }
  }
}

function scheduleNavigationPreparation() {
  if (!selectedTask.value || !selectedRoute.value) return;
  void prepareNavigationSession();
}

function setCockpitSection(section) {
  activeView.value = "cockpit";
  activeCockpitSection.value = section;
}

function showSituationalView() {
  setCockpitSection("situational");
}

async function openRoutePlanning() {
  setCockpitSection("routes");
  await planRoutes();
  setCockpitSection("routes");
}

async function openVisionMatching() {
  setCockpitSection("vision");
  await runVisionMatch();
  setCockpitSection("vision");
}

async function initialize() {
  try {
    fatalError.value = "";
    loading.value = "加载任务";
    tasks.value = await api.tasks();
    const taskId = tasks.value[0]?.id;
    if (!taskId) {
      fatalError.value = "后端未返回任务列表。";
      return;
    }

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
    void runVisionMatch({ silent: true });
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
  if (!selectedTask.value) return;
  await runAction("规划航线", async () => {
    clearPreparedNavigation();
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
    scheduleNavigationPreparation();
  });
}

async function analyzeSelectedRoute() {
  if (!selectedTask.value || !selectedRoute.value) return;
  riskAnalysis.value = await api.analyzeRisk({
    task_id: selectedTask.value.id,
    route: selectedRoute.value,
  });
}

function previewTaskEndpoints(endpoints) {
  endpointEditDraft.value = endpoints;
}

async function reloadTaskEndpoints() {
  if (!selectedTask.value || !taskDetail.value) return;
  await runAction("重载起终点", async () => {
    endpointSaveError.value = "";
    const detail = await api.taskDetail(selectedTask.value.id);
    taskDetail.value = detail;
    endpointEditDraft.value = null;
    await planRoutes();
  });
}

async function saveTaskEndpoints(endpoints) {
  if (!selectedTask.value || !taskDetail.value) return;
  try {
    endpointSaveError.value = "";
    savingEndpoints.value = true;
    const saved = await api.updateTaskEndpoints(selectedTask.value.id, endpoints.start, endpoints.target);
    taskDetail.value = { ...taskDetail.value, task: saved.task };
    endpointEditDraft.value = null;
    temporaryRisk.value = null;
    replannedRoute.value = null;
    visionResult.value = null;
    visualLocalization.value = null;
    visionMatchCache.value = {};
    visualLocalizationCache.value = {};
    await planRoutes();
    await loadVisionFrameworkData(saved.task.id);
    void runVisionMatch({ silent: true });
  } catch (err) {
    endpointSaveError.value = messageFromError(err);
  } finally {
    savingEndpoints.value = false;
  }
}

function previewRiskZones(zones) {
  riskEditDraft.value = zones;
}

async function reloadRiskZones() {
  if (!selectedTask.value || !taskDetail.value) return;
  await runAction("重载风险区", async () => {
    riskSaveError.value = "";
    const zones = await api.riskZones(selectedTask.value.id);
    taskDetail.value = { ...taskDetail.value, risk_zones: zones };
    riskEditDraft.value = null;
    await analyzeSelectedRoute();
  });
}

async function saveRiskZones(zones) {
  if (!selectedTask.value || !taskDetail.value) return;
  try {
    riskSaveError.value = "";
    savingRiskZones.value = true;
    const saved = await api.updateRiskZones(selectedTask.value.id, zones);
    taskDetail.value = { ...taskDetail.value, risk_zones: saved.risk_zones };
    riskEditDraft.value = null;
    temporaryRisk.value = null;
    replannedRoute.value = null;
    await analyzeSelectedRoute();
  } catch (err) {
    riskSaveError.value = messageFromError(err);
  } finally {
    savingRiskZones.value = false;
  }
}

async function selectRoute(route) {
  await runAction("校验航线", async () => {
    clearPreparedNavigation();
    resetSimulation();
    selectedRoute.value = route;
    replannedRoute.value = null;
    await analyzeSelectedRoute();
    scheduleNavigationPreparation();
  });
}

async function startSimulation() {
  if (!selectedRoute.value) {
    actionError.value = "请先选择一条候选航线。";
    return;
  }
  if (isSimulationStarting.value) return;
  isSimulationStarting.value = true;
  await runAction("启动任务推演", async () => {
    navigationPreparationMessage.value = preparedNavigationKey.value === navigationSessionKey()
      ? "正在载入已准备的推演时间线..."
      : "正在生成推演时间线，首次启动可能需要十几秒...";
    navigationSession.value = await prepareNavigationSession({ silent: false });
    navigationTimeline.value = navigationSession.value.timeline || [];
    navigationState.value = navigationTimeline.value[0] || null;
    simulation.value = {
      simulation_id: navigationSession.value.session_id,
      events: navigationSession.value.events,
      state: navigationSession.value.state,
    };
    simProgress.value = 0;
    temporaryRisk.value = null;
    replannedRoute.value = null;
    simLogCollapsed.value = false;
    navigationPreparationMessage.value = "推演已启动";
  });
  isSimulationStarting.value = false;
}

async function toggleAutoPlay() {
  if (playFrame.value) {
    stopAutoPlay();
    return;
  }
  if (!simulation.value) {
    await startSimulation();
    if (!simulation.value) return;
  }
  playLastTimestamp = performance.now();
  playFrame.value = requestAnimationFrame(stepAutoPlay);
}

function stepAutoPlay(timestamp) {
  const deltaSeconds = Math.max(0, (timestamp - playLastTimestamp) / 1000);
  playLastTimestamp = timestamp;
  simProgress.value = Math.min(100, simProgress.value + (deltaSeconds / SIM_PLAY_SECONDS) * 100);
  updateNavigationFrameFromProgress();
  if (simProgress.value >= 100) {
    stopAutoPlay();
    return;
  }
  playFrame.value = requestAnimationFrame(stepAutoPlay);
}

function stopAutoPlay() {
  if (!playFrame.value) return;
  cancelAnimationFrame(playFrame.value);
  playFrame.value = null;
}

function jumpSimulationToTime(timeS) {
  if (!navigationTimeline.value.length) return false;
  const duration = navigationSession.value?.duration_s || navigationTimeline.value[navigationTimeline.value.length - 1]?.time_s || 1;
  simProgress.value = Math.max(0, Math.min(100, (timeS / duration) * 100));
  navigationState.value = interpolatedNavigationFrame(timeS);
  playLastTimestamp = performance.now();
  return true;
}

function advanceSimulation() {
  if (!simulation.value) {
    actionError.value = "请先启动任务推演。";
    return;
  }
  simProgress.value = Math.min(100, simProgress.value + 8);
  updateNavigationFrameFromProgress();
}

function resetSimulation() {
  stopAutoPlay();
  simProgress.value = 0;
  navigationSession.value = null;
  navigationState.value = null;
  navigationTimeline.value = [];
  temporaryRisk.value = null;
  replannedRoute.value = null;
  simulation.value = null;
}

function startReportLoading() {
  if (reportLoadingTimer) {
    clearTimeout(reportLoadingTimer);
  }
  reportLoading.value = true;
  reportLoadingMessage.value = "正在生成任务报告...";
  reportLoadingTimer = setTimeout(() => {
    reportLoadingMessage.value = "正在汇总航线、风险、视觉匹配和导航质量数据...";
  }, 1200);
}

function stopReportLoading() {
  if (reportLoadingTimer) {
    clearTimeout(reportLoadingTimer);
    reportLoadingTimer = null;
  }
  reportLoading.value = false;
  reportLoadingMessage.value = "";
}

function navigationTrail(field) {
  if (!navigationTimeline.value.length) return [];
  const trail = navigationTimeline.value
    .filter((frame) => frame.time_s <= elapsedSeconds.value)
    .map((frame) => poseToPoint(frame[field]))
    .filter(Boolean);
  const current = poseToPoint(navigationState.value?.[field]);
  if (current && !samePoint(trail[trail.length - 1], current)) {
    trail.push(current);
  }
  return trail;
}

function updateNavigationFrameFromProgress() {
  if (!navigationTimeline.value.length) return;
  const duration = navigationSession.value?.duration_s || navigationTimeline.value[navigationTimeline.value.length - 1]?.time_s || 1;
  const targetTime = (simProgress.value / 100) * duration;
  navigationState.value = interpolatedNavigationFrame(targetTime);
}

function nearestNavigationFrame(timeS) {
  if (!navigationTimeline.value.length) return null;
  return navigationTimeline.value.reduce((best, frame) => {
    if (!best) return frame;
    return Math.abs(frame.time_s - timeS) < Math.abs(best.time_s - timeS) ? frame : best;
  }, null);
}

function interpolatedNavigationFrame(timeS) {
  if (!navigationTimeline.value.length) return null;
  const first = navigationTimeline.value[0];
  const last = navigationTimeline.value[navigationTimeline.value.length - 1];
  if (timeS <= first.time_s) return first;
  if (timeS >= last.time_s) return last;

  const afterIndex = navigationTimeline.value.findIndex((frame) => frame.time_s >= timeS);
  const after = navigationTimeline.value[afterIndex];
  const before = navigationTimeline.value[Math.max(0, afterIndex - 1)];
  if (!before || !after || before.time_s === after.time_s) return after || before;

  const ratio = (timeS - before.time_s) / (after.time_s - before.time_s);
  const exactFrame = navigationTimeline.value.find((frame) => Math.round(frame.time_s) === Math.round(timeS));
  const active = exactFrame || (ratio >= 0.5 ? after : before) || nearestNavigationFrame(timeS);
  return {
    ...active,
    time_s: Math.round(timeS),
    reference_position: interpolatePose(before.reference_position, after.reference_position, ratio),
    fused_position: interpolatePose(before.fused_position, after.fused_position, ratio),
    deviation_m: Math.round(lerp(before.deviation_m || 0, after.deviation_m || 0, ratio) * 10) / 10,
    telemetry: interpolateTelemetry(before.telemetry, after.telemetry, ratio, timeS),
    events: navigationSession.value?.events?.filter((event) => Math.round(event.time_s) === Math.round(timeS)) || [],
    active_event: navigationSession.value?.events?.filter((event) => event.time_s <= timeS).slice(-1)[0] || null,
  };
}

function interpolatePose(before, after, ratio) {
  if (!before || !after) return before || after || null;
  return {
    lon: Number(lerp(before.lon, after.lon, ratio).toFixed(6)),
    lat: Number(lerp(before.lat, after.lat, ratio).toFixed(6)),
    altitude_m: Number(lerp(before.altitude_m, after.altitude_m, ratio).toFixed(1)),
  };
}

function interpolateTelemetry(before, after, ratio, timeS) {
  if (!before || !after) return before || after || {};
  return {
    ...before,
    speed_mps: Number(lerp(before.speed_mps || 0, after.speed_mps || 0, ratio).toFixed(1)),
    heading_deg: Math.round(interpolateDegrees(before.heading_deg || 0, after.heading_deg || 0, ratio)),
    pitch_deg: Number(lerp(before.pitch_deg || 0, after.pitch_deg || 0, ratio).toFixed(1)),
    roll_deg: Number(lerp(before.roll_deg || 0, after.roll_deg || 0, ratio).toFixed(1)),
    yaw_deg: Math.round(interpolateDegrees(before.yaw_deg || 0, after.yaw_deg || 0, ratio)),
    battery_pct: Math.round(lerp(before.battery_pct || 0, after.battery_pct || 0, ratio)),
    flight_time: formatClock(timeS),
  };
}

function interpolateDegrees(before, after, ratio) {
  const delta = ((((after - before) % 360) + 540) % 360) - 180;
  return (((before + delta * ratio) % 360) + 360) % 360;
}

async function triggerTemporaryRisk() {
  if (!canTriggerReplan.value) {
    actionError.value = "请先启动任务推演，再触发动态重规划。";
    return;
  }
  await runAction("动态重规划", async () => {
    const point = currentPoint.value || selectedRoute.value.points[Math.floor(selectedRoute.value.points.length / 2)];
    const timeS = elapsedSeconds.value;
    temporaryRisk.value = await api.temporaryRisk(simulation.value.simulation_id, {
      task_id: selectedTask.value.id,
      current_position: point,
      time_s: timeS,
    });
    replannedRoute.value = navigationSession.value
      ? await api.navigationReplan({
          session_id: navigationSession.value.session_id,
          time_s: timeS + 8,
          temporary_risks: [temporaryRisk.value.risk],
        })
      : await api.replan({
          task_id: selectedTask.value.id,
          current_position: point,
          target: selectedTask.value.target,
          temporary_risks: [temporaryRisk.value.risk],
          time_s: timeS + 8,
        });
  });
}

function visionCacheKey(imageId) {
  return `${selectedTask.value?.id || "task_001"}|${imageId}|${visionTopK.value}`;
}

function applyImmediateVisionMatch(imageId) {
  const key = visionCacheKey(imageId);
  const cachedMatch = visionMatchCache.value[key];
  const cachedLocalization = visualLocalizationCache.value[key];
  visionResult.value = cachedMatch || buildInstantVisionMatch(imageId);
  visualLocalization.value = cachedLocalization || null;
}

function buildInstantVisionMatch(imageId) {
  const image = visionImages.value.find((item) => item.id === imageId) || selectedVisionImage.value;
  const sourceTileId = image?.source_tile_id;
  const rankedTiles = rankTilesNearSource(sourceTileId).slice(0, visionTopK.value);
  return {
    match_id: `instant_${imageId}`,
    task_id: selectedTask.value?.id || "task_001",
    image_id: imageId,
    query_image: image?.query_image || "",
    provider: "前端即时粗匹配预测",
    status: "preview",
    algorithm_trace: ["source_tile_id", "grid_neighbor_prefill", "async_refine"],
    candidates: rankedTiles.map((tile, index) => ({
      tile_id: tile.tile_id,
      confidence: index === 0 ? 0.82 : Math.max(0.42, 0.7 - index * 0.08),
      matched_points: index === 0 ? 96 : Math.max(42, 82 - index * 12),
      inlier_ratio: index === 0 ? 0.62 : Math.max(0.32, 0.52 - index * 0.06),
      bbox: tile.bbox,
      center: tile.center,
      offset_m: [0, 0],
      status: index === 0 ? "best" : "candidate",
      reason: "基于当前影像帧源瓦片和相邻网格即时预显示，后台接口返回后自动精修。",
      rank: index + 1,
      preview: true,
    })),
    candidate_count: rankedTiles.length,
    total_candidate_count: rankedTiles.length,
    preview: true,
  };
}

function rankTilesNearSource(sourceTileId) {
  if (!visionTiles.value.length) return [];
  const source = visionTiles.value.find((tile) => tile.tile_id === sourceTileId) || visionTiles.value[0];
  const sourceRow = source?.grid?.row || 0;
  const sourceCol = source?.grid?.col || 0;
  return [...visionTiles.value].sort((tileA, tileB) => {
    const distanceA = tileGridDistance(tileA, sourceRow, sourceCol);
    const distanceB = tileGridDistance(tileB, sourceRow, sourceCol);
    if (distanceA !== distanceB) return distanceA - distanceB;
    return String(tileA.tile_id).localeCompare(String(tileB.tile_id));
  });
}

function tileGridDistance(tile, row, col) {
  const tileRow = tile?.grid?.row || row;
  const tileCol = tile?.grid?.col || col;
  return Math.abs(tileRow - row) + Math.abs(tileCol - col);
}

async function runVisionMatch(options = {}) {
  const execute = async () => {
    const imageId = visionImages.value.some((image) => image.id === selectedVisionImageId.value)
      ? selectedVisionImageId.value
      : visionImages.value[0]?.id || "demo_uav_001";
    selectedVisionImageId.value = imageId;
    applyImmediateVisionMatch(imageId);

    const key = visionCacheKey(imageId);
    const basePayload = {
      task_id: selectedTask.value?.id || "task_001",
      image_id: imageId,
    };
    const token = ++visionRequestToken;

    const matchPromise = pendingVisionMatchRequests.get(key) || api
      .visionMatch({
        ...basePayload,
        top_k: visionTopK.value,
        algorithm_mode: "precomputed",
      })
      .finally(() => pendingVisionMatchRequests.delete(key));
    pendingVisionMatchRequests.set(key, matchPromise);

    const match = await matchPromise;
    visionMatchCache.value = { ...visionMatchCache.value, [key]: match };
    if (token === visionRequestToken && selectedVisionImageId.value === imageId) {
      visionResult.value = match;
    }

    const localizationPromise = pendingVisualLocalizationRequests.get(key) || api
      .visionLocalize({
        ...basePayload,
        top_k_tiles: visionTopK.value,
        matcher_mode: "precomputed_proxy",
        lighting_options: lightingOptions.value,
      })
      .catch(() => null)
      .finally(() => pendingVisualLocalizationRequests.delete(key));
    pendingVisualLocalizationRequests.set(key, localizationPromise);

    const localization = await localizationPromise;
    if (localization) {
      visualLocalizationCache.value = { ...visualLocalizationCache.value, [key]: localization };
    }
    if (token === visionRequestToken && selectedVisionImageId.value === imageId) {
      visualLocalization.value = localization;
    }
  };

  if (options.silent) {
    try {
      await execute();
    } catch (err) {
      console.warn("视觉匹配更新失败", err);
    }
    return;
  }
  await runAction("视觉匹配", execute);
}

async function selectVisionImage(imageId) {
  const image = visionImages.value.find((item) => item.id === imageId);
  selectedVisionImageId.value = imageId;
  if (image?.capture_time_s !== undefined && navigationTimeline.value.length) {
    jumpSimulationToTime(image.capture_time_s);
  }
  applyImmediateVisionMatch(imageId);
  await runVisionMatch();
}

async function loadReport() {
  if (!selectedTask.value) return;
  if (reportLoading.value) return;
  startReportLoading();
  try {
    await runAction("生成报告", async () => {
      reportResult.value = await api.report(selectedTask.value.id);
      activeView.value = "report";
    });
  } finally {
    stopReportLoading();
  }
}

async function refreshSuperMapStatus() {
  await runAction("检测 SuperMap 服务", async () => {
    const [supermap, supermapRuntime] = await Promise.all([
      api.supermapConfig().catch(() => supermapConfig.value),
      api.supermapStatus(),
    ]);
    supermapConfig.value = supermap;
    supermapStatus.value = supermapRuntime;
  });
}

function confidencePercent(value) {
  return `${Math.round((value || 0) * 100)}%`;
}

function evidenceSrc(url) {
  if (!url) return "";
  if (url.startsWith("/api/")) return `${API_ORIGIN}${url}`;
  return url;
}

function lightingValue(key, fallback = "-") {
  const lighting = visualLocalization.value?.image_simulation?.lighting_model || selectedVisionImage.value?.uav_frame_simulation?.lighting_model;
  const value = lighting?.[key];
  return value === undefined || value === null || value === "" ? fallback : value;
}

function poseToPoint(pose) {
  if (!pose) return null;
  return [pose.lon, pose.lat, pose.altitude_m];
}

function lerp(start, end, ratio) {
  return start + (end - start) * Math.max(0, Math.min(1, ratio));
}

function samePoint(a, b) {
  if (!a || !b) return false;
  return a.every((value, index) => Math.abs(value - b[index]) < 0.000001);
}

function formatClock(totalSeconds) {
  const rounded = Math.max(0, Math.round(totalSeconds || 0));
  const minutes = Math.floor(rounded / 60);
  const seconds = rounded % 60;
  return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
}

function locationSourceLabel(source) {
  return {
    reference_route: "参考航线",
    visual_fusion: "视觉融合",
    visual_assisted: "视觉辅助",
    manual_review: "人工复核",
  }[source] || "待命";
}

function navigationModeLabel(mode) {
  return {
    autonomous: "自主",
    assisted: "辅助",
    review: "复核",
    waiting: "待命",
  }[mode] || "待命";
}

function runtimeStatusLabel(status) {
  if (status === "verified") return "已验证";
  if (status === "optional") return "可选";
  if (status === "missing") return "缺失";
  if (status === "not_checked") return "未检测";
  if (status === "checking") return "检测中";
  return status || "检测中";
}

function localizationStatusLabel(status) {
  if (status === "localized") return "已定位";
  if (status === "needs_review") return "需复核";
  if (status === "matched") return "已匹配";
  if (status === "failed") return "定位失败";
  return status || "等待定位";
}

function chineseDisplay(value) {
  return String(value || "").replaceAll("UAV", "无人机").replaceAll("uav", "无人机");
}

function formatPoint(point) {
  if (!point) return "未触发";
  return `${point[0].toFixed(5)}, ${point[1].toFixed(5)}, ${Math.round(point[2] || 0)}米`;
}

onMounted(initialize);
onBeforeUnmount(() => {
  stopAutoPlay();
  stopReportLoading();
});

watch(navigationMode, () => {
  clearPreparedNavigation();
  resetSimulation();
  scheduleNavigationPreparation();
});

watch(activeVisionImageId, async (imageId, previousImageId) => {
  if (!imageId || imageId === previousImageId) return;
  const alreadySelected = selectedVisionImageId.value === imageId;
  selectedVisionImageId.value = imageId;
  if (alreadySelected) return;
  await runVisionMatch({ silent: true });
});
</script>

<template>
  <ReportPage
    v-if="activeView === 'report'"
    :report="reportResult"
    :risk-analysis="riskAnalysis"
    :events="events"
    :loading="Boolean(loading)"
    :error="actionError"
    @close="activeView = 'cockpit'"
    @reload="loadReport"
  />

  <main v-else class="cockpit-shell">
    <header class="cockpit-topbar">
      <div class="cockpit-brand">
        <span>2026/06/09</span>
        <strong>无人机视觉自主导航系统</strong>
        <small>{{ selectedTask?.display_name || "低空巡检示范任务" }} · {{ navigationMode === "autonomous" ? "自主导航主线" : "辅助导航模式" }}</small>
      </div>
      <nav class="cockpit-tabs">
        <button :class="{ active: activeCockpitSection === 'situational' }" @click="showSituationalView">实时态势</button>
        <button :class="{ active: activeCockpitSection === 'routes' }" @click="openRoutePlanning">航线规划</button>
        <button :class="{ active: activeCockpitSection === 'vision' }" @click="openVisionMatching">影像匹配</button>
        <button :disabled="reportLoading" @click="loadReport">{{ reportLoading ? "生成中" : "任务报告" }}</button>
      </nav>
      <div class="cockpit-status">
        <span :class="['status-dot', fatalError ? 'status-bad' : 'status-good']"></span>
        <strong>{{ cockpitStatus }}</strong>
      </div>
    </header>

    <section v-if="fatalError || actionError" class="cockpit-alert">
      {{ fatalError || actionError }}
    </section>

    <section v-if="reportLoading" class="report-loading-banner">
      <span class="loading-spinner"></span>
      <div>
        <strong>{{ reportLoadingMessage }}</strong>
        <small>报告生成时间取决于后端汇总数据量，请稍候。</small>
      </div>
    </section>

    <section class="cockpit-grid">
      <aside class="cockpit-left">
        <section class="glass-panel command-panel">
          <div class="panel-title-row">
            <h2>导航控制</h2>
            <span>{{ telemetry.mode }}</span>
          </div>
          <div class="mode-switch">
            <button :class="{ active: navigationMode === 'autonomous' }" @click="navigationMode = 'autonomous'">视觉自主</button>
            <button :class="{ active: navigationMode === 'assisted' }" @click="navigationMode = 'assisted'">辅助导航</button>
          </div>
          <div class="command-buttons">
            <button :disabled="!selectedTask" @click="planRoutes">规划</button>
            <button :disabled="!selectedRoute || isSimulationStarting" @click="startSimulation">
              {{ isSimulationStarting ? "准备中" : "推演" }}
            </button>
            <button :disabled="!selectedRoute || isSimulationStarting" @click="toggleAutoPlay">
              {{ isSimulationStarting ? "准备推演" : isPlaying ? "暂停" : "播放" }}
            </button>
            <button :disabled="!simulation" @click="advanceSimulation">步进</button>
            <button :disabled="!canTriggerReplan" @click="triggerTemporaryRisk">重规划</button>
            <button @click="resetSimulation">复位</button>
          </div>
          <small v-if="navigationPreparationMessage" class="command-hint">
            {{ navigationPreparationMessage }}
          </small>
        </section>

        <section class="glass-panel">
          <h2>图层管理</h2>
          <label v-for="layer in layers" :key="layer.id" class="layer-row">
            <input v-model="layer.visible" type="checkbox" />
            <span>{{ layer.name }}</span>
          </label>
          <label class="layer-row">
            <input v-model="showShortestRoute" type="checkbox" />
            <span>显示最短航线</span>
          </label>
          <button class="ghost-button" @click="refreshSuperMapStatus">刷新 SuperMap 状态</button>
        </section>

        <MissionEndpointEditor
          v-if="selectedTask"
          :task="taskDetailForDisplay?.task || selectedTask"
          :saving="savingEndpoints"
          :error="endpointSaveError"
          @preview="previewTaskEndpoints"
          @reload="reloadTaskEndpoints"
          @save="saveTaskEndpoints"
        />

        <RiskZoneEditor
          v-if="selectedTask"
          :task="taskDetailForDisplay?.task || selectedTask"
          :zones="taskDetail?.risk_zones || []"
          :saving="savingRiskZones"
          :error="riskSaveError"
          @preview="previewRiskZones"
          @reload="reloadRiskZones"
          @save="saveRiskZones"
        />

        <section class="glass-panel">
          <h2>全局航迹</h2>
          <div class="mini-map">
            <svg viewBox="0 0 100 70" role="img" aria-label="航迹总览">
              <polyline points="8,60 22,48 34,42 45,25 58,18 74,12 91,8" />
              <circle cx="8" cy="60" r="2.8" class="mini-start" />
              <circle cx="91" cy="8" r="3.2" class="mini-target" />
              <circle :cx="8 + simProgress * 0.83" :cy="60 - simProgress * 0.52" r="2.5" class="mini-uav" />
            </svg>
          </div>
        </section>

        <section :class="['glass-panel', activeCockpitSection === 'routes' ? 'section-focus' : '']">
          <h2>候选航线</h2>
          <button
            v-for="route in routes"
            :key="route.id"
            :class="['route-card compact', selectedRoute?.id === route.id ? 'active' : '']"
            @click="selectRoute(route)"
          >
            <strong>{{ route.name }}</strong>
            <span>{{ route.distance_m }} 米 · {{ route.score }} 分 · {{ route.risk_level }}</span>
          </button>
        </section>
      </aside>

      <section :class="['cockpit-center', activeCockpitSection === 'situational' ? 'section-focus' : '']">
        <div class="scene-frame">
          <div class="scene-head">
            <strong>{{ selectedTask?.display_name || "任务区域" }}</strong>
            <span>场景/地图/数据：{{ runtimeStatusLabel(supermapStatus?.services?.scene?.runtime_status) }}</span>
          </div>
          <SuperMapScene
            v-if="taskDetailForDisplay && selectedTask"
            :task-detail="taskDetailForDisplay"
            :selected-task="taskDetailForDisplay.task"
            :layers="layers"
            :routes="visibleSceneRoutes"
            :selected-route="selectedRoute"
            :risk-analysis="riskAnalysis"
            :temporary-risk="temporaryRisk"
            :replanned-route="replannedRoute"
            :vision-result="sceneVisionResult"
            :vision-tiles="visionTiles"
            :current-point="currentPoint"
            :actual-flight-trail="actualFlightTrail"
            :reference-flight-trail="referenceFlightTrail"
            :visual-match-points="visualMatchPoints"
            :supermap-config="supermapConfig"
          />
          <div v-if="!taskDetailForDisplay || !selectedTask" class="scene-loading">等待任务和 SuperMap 场景加载</div>
          <section v-if="simulation" :class="['simulation-log-window', simLogCollapsed ? 'collapsed' : '']">
            <button class="simulation-log-toggle" type="button" @click="simLogCollapsed = !simLogCollapsed">
              <strong>仿真日志</strong>
              <span>{{ simLogCollapsed ? "展开" : "收起" }}</span>
            </button>
            <div v-if="!simLogCollapsed" class="simulation-log-list">
              <article v-for="log in simulationLogs" :key="log.id">
                <strong>{{ log.time }}秒</strong>
                <span>{{ log.title }}</span>
                <small>{{ log.detail }}</small>
              </article>
              <article v-if="!simulationLogs.length">
                <strong>--</strong>
                <span>等待仿真推进</span>
                <small>播放或步进后显示导航、视觉融合、风险和重规划日志。</small>
              </article>
            </div>
          </section>
        </div>

        <section class="cockpit-timeline">
          <div class="progress-track">
            <span :style="{ width: `${simProgress}%` }"></span>
          </div>
          <div class="timeline-meta">
            <strong>{{ telemetry.flightTime }}</strong>
            <span>{{ Math.round(simProgress) }}%</span>
            <span>下一事件：{{ upcomingEvents[0]?.title || "暂无" }}</span>
          </div>
        </section>
      </section>

      <aside class="cockpit-right">
        <section class="glass-panel video-panel">
          <div class="video-head">
            <strong>实时影像 · {{ chineseDisplay(telemetry.uavId) }}</strong>
            <span>{{ chineseDisplay(selectedVisionImage?.name) || "无人机实时影像帧" }}</span>
          </div>
          <div class="video-feed">
            <img
              v-if="selectedVisionImage?.query_image"
              :src="selectedVisionImage.query_image"
              alt="无人机实时影像帧"
              @error="$event.target.src = '/demo/luojia_ortho_preview.jpg'"
            />
            <div v-else class="video-placeholder">无人机影像帧</div>
            <div class="video-osd">
              <span>录制</span>
              <span>{{ telemetry.altitude.toFixed(1) }}米</span>
              <span>{{ telemetry.speed.toFixed(1) }}米/秒</span>
            </div>
          </div>
          <div class="vision-select">
            <button
              v-for="(image, index) in visionImages"
              :key="image.id"
              :class="{ active: selectedVisionImageId === image.id }"
              @click="selectVisionImage(image.id)"
            >
              第 {{ index + 1 }} 帧
            </button>
          </div>
          <small class="vision-frame-source" v-if="selectedVisionImage">
            {{ selectedVisionImage.source || "auto_dem_ortho_route_sampler" }} ·
            {{ selectedVisionImage.frame_trigger || "auto" }} ·
            {{ selectedVisionImage.source_tile_id || "ortho" }}
          </small>
        </section>

        <section class="glass-panel telemetry-panel">
          <h2>飞行遥测</h2>
          <div class="telemetry-grid">
            <span>经度<strong>{{ telemetry.lon.toFixed(6) }}</strong></span>
            <span>纬度<strong>{{ telemetry.lat.toFixed(6) }}</strong></span>
            <span>高度<strong>{{ telemetry.altitude.toFixed(1) }} 米</strong></span>
            <span>速度<strong>{{ telemetry.speed.toFixed(1) }} 米/秒</strong></span>
            <span>航向<strong>{{ telemetry.heading }}°</strong></span>
            <span>电量<strong>{{ telemetry.battery }}%</strong></span>
            <span>俯仰角<strong>{{ telemetry.pitch.toFixed(1) }}°</strong></span>
            <span>横滚角<strong>{{ telemetry.roll.toFixed(1) }}°</strong></span>
            <span>偏航角<strong>{{ telemetry.yaw }}°</strong></span>
            <span>定位源<strong>{{ locationSourceLabel(visualNavigation.source) }}</strong></span>
            <span>视觉偏差<strong>{{ visualNavigation.deviationM }} 米</strong></span>
            <span>导航模式<strong>{{ navigationModeLabel(visualNavigation.status) }}</strong></span>
          </div>
          <div class="battery-bar"><span :style="{ width: `${telemetry.battery}%` }"></span></div>
        </section>

        <section :class="['glass-panel match-panel', activeCockpitSection === 'vision' ? 'section-focus' : '']">
          <h2>视觉定位状态</h2>
          <div v-if="bestVisionCandidate" class="match-card">
            <strong>{{ visualNavigation.label }} · {{ bestVisionCandidate.tile_id }}</strong>
            <span>{{ confidencePercent(bestVisionCandidate.confidence) }}</span>
            <small>匹配点 {{ bestVisionCandidate.matched_points }} · 内点 {{ confidencePercent(bestVisionCandidate.inlier_ratio) }} · 偏差 {{ visualNavigation.deviationM }} 米</small>
            <div class="confidence-bar">
              <span :style="{ width: confidencePercent(bestVisionCandidate.confidence) }"></span>
            </div>
          </div>
          <div v-if="visualLocalization" class="synthetic-compare">
            <figure>
              <img :src="visualLocalization.query_image" alt="无人机当前影像帧" />
              <figcaption>无人机图像</figcaption>
            </figure>
            <figure>
              <img :src="bestSyntheticView?.image_url || '/demo/luojia_ortho_preview.jpg'" alt="合成候选视图" />
              <figcaption>合成视图 {{ bestSyntheticView?.view_id || "-" }}</figcaption>
            </figure>
          </div>
          <div v-if="visualLocalization" class="synthetic-metrics">
            <span>误差半径<strong>{{ visualLocalization.error_radius_m }} 米</strong></span>
            <span>修正向量<strong>{{ visualLocalization.correction_vector_m.join(" / ") }} 米</strong></span>
            <span>定位状态<strong>{{ localizationStatusLabel(visualLocalization.status) }}</strong></span>
          </div>
          <p v-if="!bestVisionCandidate && !visualLocalization" class="summary-text">等待无人机影像帧进入匹配流程。</p>
          <div v-if="visualLocalization" class="provider-metrics">
            <span>匹配器<strong>{{ visualLocalization.provider }}</strong></span>
            <span>太阳角<strong>{{ lightingValue("sun_azimuth_deg") }} / {{ lightingValue("sun_elevation_deg") }}</strong></span>
          </div>
          <div class="lighting-controls">
            <label>
              <span>时间</span>
              <input v-model="lightingOptions.capture_datetime" type="datetime-local" @change="runVisionMatch" />
            </label>
            <label>
              <span>曝光</span>
              <input v-model.number="lightingOptions.exposure_ev" type="range" min="-2" max="2" step="0.1" @change="runVisionMatch" />
            </label>
            <label>
              <span>阴影</span>
              <input v-model.number="lightingOptions.shadow_strength" type="range" min="0" max="0.75" step="0.05" @change="runVisionMatch" />
            </label>
            <label>
              <span>雾化</span>
              <input v-model.number="lightingOptions.haze" type="range" min="0" max="0.6" step="0.05" @change="runVisionMatch" />
            </label>
            <label>
              <span>色温</span>
              <input v-model.number="lightingOptions.color_temperature_k" type="range" min="3200" max="8500" step="100" @change="runVisionMatch" />
            </label>
          </div>
          <div v-if="activeOrbEvidence" class="orb-evidence-grid">
            <figure>
              <img :src="evidenceSrc(activeOrbEvidence.match_lines)" alt="ORB 匹配连线" />
              <figcaption>ORB 匹配</figcaption>
            </figure>
            <figure>
              <img :src="evidenceSrc(activeOrbEvidence.ransac_inliers)" alt="RANSAC 内点匹配" />
              <figcaption>RANSAC 内点</figcaption>
            </figure>
          </div>
          <div v-if="navigationState" class="position-fusion-list">
            <span>参考<strong>{{ formatPoint(visualNavigation.referencePoint) }}</strong></span>
            <span>视觉<strong>{{ formatPoint(visualNavigation.visualPoint) }}</strong></span>
            <span>融合<strong>{{ formatPoint(visualNavigation.estimatedPoint) }}</strong></span>
          </div>
        </section>

        <section class="glass-panel">
          <h2>参考航线与安全约束</h2>
          <div class="kpi-row">
            <span>航程<strong>{{ routeSummary.distance }}</strong></span>
            <span>评分<strong>{{ routeSummary.score }}</strong></span>
            <span>风险<strong>{{ routeSummary.risk }}</strong></span>
          </div>
          <p class="summary-text">{{ riskAnalysis?.summary || "航线风险分析等待生成。" }}</p>
        </section>

        <section class="glass-panel">
          <h2>自主/辅助边界</h2>
          <p class="summary-text">
            视觉自主模式下，匹配结果会修正无人机导航状态；辅助导航模式下，匹配结果只作为定位参考和人工复核提示。
          </p>
        </section>
      </aside>
    </section>

    <footer v-if="!simulation" class="event-console">
      <section>
        <h2>实时事件流</h2>
        <div class="console-list">
          <article v-for="event in activeEvents" :key="`${event.type}-${event.time_s}`">
            <strong>{{ event.time_s }}秒</strong>
            <span>{{ event.title }}</span>
            <small>{{ event.description }}</small>
          </article>
          <article v-if="!activeEvents.length">
            <strong>--</strong>
            <span>等待任务推演</span>
            <small>点击播放后，视觉匹配、风险告警和重规划事件将随时间推进。</small>
          </article>
        </div>
      </section>
    </footer>
  </main>
</template>

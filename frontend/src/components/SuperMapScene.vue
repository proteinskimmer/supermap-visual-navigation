<script setup>
import { computed } from "vue";
import MockMissionMap from "./MockMissionMap.vue";

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
});

const sceneProvider = import.meta.env.VITE_SCENE_PROVIDER || "mock";

const sceneServices = computed(() =>
  props.layers
    .filter((layer) => layer.service_url)
    .map((layer) => ({
      id: layer.id,
      name: layer.name,
      url: layer.service_url,
    }))
);
</script>

<template>
  <div class="scene-shell">
    <div v-if="sceneProvider === 'supermap'" class="supermap-placeholder">
      <div class="supermap-mount" data-supermap-mount></div>
      <div class="supermap-empty-state">
        <strong>SuperMap iClient3D 接入点</strong>
        <span>配置 iServer 三维服务后，在本组件挂载真实 Cesium/SuperMap 场景。</span>
        <small v-if="sceneServices.length">
          已读取 {{ sceneServices.length }} 个服务地址，可从 layers[].service_url 接入。
        </small>
        <small v-else>当前 demo 数据尚未填写 iServer service_url，自动保留 mock 态势图作为备用。</small>
      </div>
      <MockMissionMap
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

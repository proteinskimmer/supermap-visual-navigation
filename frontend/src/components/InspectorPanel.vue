<script setup>
import { computed } from "vue";
import ElevationProfile from "./ElevationProfile.vue";
import EmptyState from "./EmptyState.vue";

const props = defineProps({
  routes: { type: Array, default: () => [] },
  selectedRoute: { type: Object, default: null },
  riskAnalysis: { type: Object, default: null },
  visionResult: { type: Object, default: null },
  selectedVisionImage: { type: Object, default: null },
  bestVisionCandidate: { type: Object, default: null },
  visionTiles: { type: Array, default: () => [] },
  visionTopK: { type: Number, default: 3 },
});

defineEmits(["select-route", "update-vision-top-k", "run-vision-match"]);

const traceLabels = {
  image_normalize: "图像预处理",
  tile_retrieve_top3: "瓦片粗检索",
  local_feature_match: "局部特征匹配",
  ransac_verify: "RANSAC 验证",
  manual_review_required: "人工复核",
};

const tileSources = computed(() => {
  const sources = new Set(props.visionTiles.map((tile) => tile.source));
  return Array.from(sources);
});

const totalFeatureCount = computed(() =>
  props.visionTiles.reduce((total, tile) => total + (tile.feature_count || 0), 0)
);

function percent(value) {
  return `${Math.round((value || 0) * 100)}%`;
}

function statusLabel(status) {
  if (status === "best") return "最优";
  if (status === "candidate") return "候选";
  if (status === "needs_review") return "复核";
  if (status === "rejected") return "剔除";
  if (status === "matched") return "已匹配";
  if (status === "precomputed") return "预计算";
  return status;
}

function providerLabel(provider) {
  if (provider === "precomputed") return "预计算结果";
  return provider || "未知算法";
}
</script>

<template>
  <aside class="inspector">
    <section class="panel-section">
      <h2>候选航线</h2>
      <EmptyState v-if="!routes.length" title="暂无航线" message="点击规划后生成三条候选航线。" />
      <button
        v-for="route in routes"
        v-else
        :key="route.id"
        :class="['route-card', selectedRoute?.id === route.id ? 'active' : '']"
        @click="$emit('select-route', route)"
      >
        <strong>{{ route.name }}</strong>
        <span>{{ route.distance_m }} 米 · {{ route.score }} 分 · {{ route.risk_level }}</span>
        <small>{{ route.strategy }}</small>
      </button>
    </section>

    <section class="panel-section" v-if="riskAnalysis">
      <h2>风险校验</h2>
      <div class="score-row">
        <strong>{{ riskAnalysis.score }}</strong>
        <span>{{ riskAnalysis.risk_level }}</span>
      </div>
      <p class="summary-text">{{ riskAnalysis.summary }}</p>
      <ul class="risk-list">
        <li v-for="segment in riskAnalysis.segments.slice(0, 4)" :key="segment.segment_id">
          {{ segment.reason }}
        </li>
        <li v-if="!riskAnalysis.segments.length">当前航线未发现高风险航段</li>
      </ul>
    </section>
    <EmptyState v-else title="未校验风险" message="选择或生成航线后自动执行风险分析。" />

    <ElevationProfile :profile="riskAnalysis?.profile || []" />

    <section class="panel-section" v-if="visionResult">
      <h2>视觉匹配</h2>
      <div class="vision-preview">
        <div class="vision-placeholder">
          <strong>{{ selectedVisionImage?.id || visionResult.image_id }}</strong>
          <span>{{ selectedVisionImage?.query_image || visionResult.query_image }}</span>
        </div>
        <div class="vision-preview-meta">
          <span>{{ selectedVisionImage?.resolution?.join(" x ") || "1280 x 720" }}</span>
          <span>{{ selectedVisionImage?.camera?.height_m || "-" }} 米</span>
          <span>{{ selectedVisionImage?.scene_tags?.join(" / ") }}</span>
        </div>
      </div>
      <div class="vision-query">
        <strong>{{ selectedVisionImage?.name || visionResult.image_id }}</strong>
        <span>{{ providerLabel(visionResult.provider) }} · {{ statusLabel(visionResult.status) }} · {{ visionResult.candidate_count }}/{{ visionResult.total_candidate_count }}</span>
        <small v-if="bestVisionCandidate">
          最优候选 {{ bestVisionCandidate.tile_id }}，偏移
          {{ bestVisionCandidate.offset_m[0] }}米 / {{ bestVisionCandidate.offset_m[1] }}米
        </small>
      </div>
      <div class="segmented-control">
        <button
          v-for="topK in [1, 2, 3]"
          :key="topK"
          :class="{ active: visionTopK === topK }"
          @click="$emit('update-vision-top-k', topK)"
        >
          前 {{ topK }} 个
        </button>
        <button @click="$emit('run-vision-match')">刷新</button>
      </div>
      <div class="vision-box">
        <div v-for="candidate in visionResult.candidates" :key="candidate.tile_id" class="candidate-row">
          <span>#{{ candidate.rank }} {{ candidate.tile_id }} · {{ statusLabel(candidate.status) }}</span>
          <strong>{{ Math.round(candidate.confidence * 100) }}%</strong>
          <small>{{ candidate.matched_points }} 点</small>
          <div class="confidence-bar">
            <span :style="{ width: percent(candidate.confidence) }"></span>
          </div>
          <div class="candidate-metrics">
            <span>内点 {{ percent(candidate.inlier_ratio) }}</span>
            <span>偏移 {{ candidate.offset_m[0] }} / {{ candidate.offset_m[1] }} 米</span>
          </div>
          <em>{{ candidate.reason }}</em>
        </div>
      </div>
      <div class="vision-trace vision-trace-timeline">
        <span v-for="step in visionResult.algorithm_trace" :key="step">{{ traceLabels[step] || step }}</span>
      </div>
      <div class="tile-debug">
        <strong>瓦片索引</strong>
        <span>{{ visionTiles.length }} 个候选瓦片 · {{ totalFeatureCount }} 个预计算特征</span>
        <small>{{ tileSources.join(" / ") || "未加载瓦片来源" }}</small>
      </div>
    </section>
    <EmptyState v-else title="视觉结果未加载" message="视觉匹配可后置，不影响航线仿真主流程。" />
  </aside>
</template>

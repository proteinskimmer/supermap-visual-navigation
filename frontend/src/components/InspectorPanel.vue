<script setup>
import ElevationProfile from "./ElevationProfile.vue";
import EmptyState from "./EmptyState.vue";

defineProps({
  routes: { type: Array, default: () => [] },
  selectedRoute: { type: Object, default: null },
  riskAnalysis: { type: Object, default: null },
  visionResult: { type: Object, default: null },
  selectedVisionImage: { type: Object, default: null },
  bestVisionCandidate: { type: Object, default: null },
});

defineEmits(["select-route"]);
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
        <span>{{ route.distance_m }} m · {{ route.score }} 分 · {{ route.risk_level }}</span>
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
      <div class="vision-query">
        <strong>{{ selectedVisionImage?.name || visionResult.image_id }}</strong>
        <span>{{ visionResult.provider }} · {{ visionResult.status }}</span>
        <small v-if="bestVisionCandidate">
          最优候选 {{ bestVisionCandidate.tile_id }}，偏移
          {{ bestVisionCandidate.offset_m[0] }}m / {{ bestVisionCandidate.offset_m[1] }}m
        </small>
      </div>
      <div class="vision-box">
        <div v-for="candidate in visionResult.candidates" :key="candidate.tile_id" class="candidate-row">
          <span>#{{ candidate.rank }} {{ candidate.tile_id }}</span>
          <strong>{{ Math.round(candidate.confidence * 100) }}%</strong>
          <small>{{ candidate.matched_points }} pts</small>
          <em>{{ candidate.reason }}</em>
        </div>
      </div>
      <div class="vision-trace">
        <span v-for="step in visionResult.algorithm_trace" :key="step">{{ step }}</span>
      </div>
    </section>
    <EmptyState v-else title="视觉结果未加载" message="视觉匹配可后置，不影响航线仿真主流程。" />
  </aside>
</template>

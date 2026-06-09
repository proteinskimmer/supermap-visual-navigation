<script setup>
import { computed } from "vue";
import EmptyState from "./EmptyState.vue";

const props = defineProps({
  profile: { type: Array, default: () => [] },
});

const chart = computed(() => {
  if (!props.profile.length) return { terrain: "", flight: "", minHeight: 0, maxHeight: 0, maxDistance: 0 };
  const maxDistance = Math.max(...props.profile.map((item) => item.distance_m), 1);
  const heights = props.profile.flatMap((item) => [item.terrain_height_m, item.flight_height_m]);
  const minHeight = Math.min(...heights);
  const maxHeight = Math.max(...heights);

  function toPoint(item, key) {
    const x = (item.distance_m / maxDistance) * 100;
    const y = 100 - ((item[key] - minHeight) / (maxHeight - minHeight || 1)) * 100;
    return `${x.toFixed(2)},${y.toFixed(2)}`;
  }

  return {
    terrain: props.profile.map((item) => toPoint(item, "terrain_height_m")).join(" "),
    flight: props.profile.map((item) => toPoint(item, "flight_height_m")).join(" "),
    minHeight,
    maxHeight,
    maxDistance,
  };
});

const stats = computed(() => {
  if (!props.profile.length) return null;
  const clearances = props.profile.map((item) => item.flight_height_m - item.terrain_height_m);
  return {
    samples: props.profile.length,
    minClearance: Math.min(...clearances),
    maxTerrain: Math.max(...props.profile.map((item) => item.terrain_height_m)),
    maxDistance: chart.value.maxDistance,
  };
});
</script>

<template>
  <section class="panel-section">
    <h2>高程剖面</h2>
    <EmptyState
      v-if="!profile.length"
      title="暂无剖面"
      message="选择航线并完成风险校验后显示地形和飞行高度。"
    />
    <div v-else class="profile-panel">
      <svg class="profile-chart profile-chart-large" viewBox="0 0 100 100" role="img" aria-label="高程剖面">
        <polyline points="0,86 100,86" class="profile-axis" />
        <polyline :points="chart.terrain" class="profile-terrain-line" />
        <polyline :points="chart.flight" class="profile-line" />
      </svg>
      <div class="profile-legend">
        <span><i class="legend-flight"></i>飞行高度</span>
        <span><i class="legend-terrain"></i>地形高程</span>
      </div>
      <div class="profile-stats" v-if="stats">
        <span>采样点<strong>{{ stats.samples }}</strong></span>
        <span>最小离地<strong>{{ Math.round(stats.minClearance) }} 米</strong></span>
        <span>最高地形<strong>{{ Math.round(stats.maxTerrain) }} 米</strong></span>
        <span>剖面长度<strong>{{ Math.round(stats.maxDistance) }} 米</strong></span>
      </div>
    </div>
  </section>
</template>

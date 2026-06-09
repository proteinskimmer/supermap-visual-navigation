<script setup>
import { computed } from "vue";

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
});

const bounds = computed(() => {
  const ring = props.selectedTask?.area?.coordinates?.[0] || [];
  const lons = ring.map((point) => point[0]);
  const lats = ring.map((point) => point[1]);
  return {
    minLon: Math.min(...lons),
    maxLon: Math.max(...lons),
    minLat: Math.min(...lats),
    maxLat: Math.max(...lats),
  };
});

const riskHighlightSegments = computed(() => {
  if (!props.selectedRoute || !props.riskAnalysis?.segments?.length) return [];
  return props.riskAnalysis.segments
    .map((segment) => props.selectedRoute.points.slice(segment.start_index, segment.end_index + 1))
    .filter((points) => points.length >= 2);
});

function isLayerVisible(layerId) {
  return props.layers.find((layer) => layer.id === layerId)?.visible;
}

function project(point) {
  const box = bounds.value;
  const x = ((point[0] - box.minLon) / (box.maxLon - box.minLon || 1)) * 100;
  const y = (1 - (point[1] - box.minLat) / (box.maxLat - box.minLat || 1)) * 100;
  return `${x},${y}`;
}

function pointsAttr(points) {
  return points.map(project).join(" ");
}

function riskClass(level) {
  if (level >= 5) return "risk-critical";
  if (level >= 4) return "risk-high";
  return "risk-medium";
}

function routeClass(route) {
  if (!route) return "";
  if (route.id === props.selectedRoute?.id) return "selected-route";
  if (route.mode === "shortest") return "route-shortest";
  if (route.mode === "safest") return "route-safest";
  return "route-balanced";
}

function candidateClass(candidate) {
  if (candidate.status === "best") return "vision-best";
  if (candidate.status === "rejected") return "vision-rejected";
  return "vision-candidate";
}
</script>

<template>
  <svg viewBox="0 0 100 100" class="mission-map" role="img" aria-label="任务态势图">
    <defs>
      <pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse">
        <path d="M 10 0 L 0 0 0 10" fill="none" stroke="#d8e1ea" stroke-width="0.25" />
      </pattern>
    </defs>
    <rect width="100" height="100" fill="#f4f8fb" />
    <rect width="100" height="100" fill="url(#grid)" />
    <polygon :points="pointsAttr(selectedTask.area.coordinates[0])" class="task-area" />

    <g v-if="isLayerVisible('risk_zone')">
      <polygon
        v-for="zone in taskDetail.risk_zones"
        :key="zone.id"
        :points="pointsAttr(zone.polygon)"
        :class="['risk-zone', riskClass(zone.level)]"
      />
    </g>

    <g v-if="temporaryRisk">
      <polygon :points="pointsAttr(temporaryRisk.risk.polygon)" class="risk-zone temp-risk" />
    </g>

    <g v-if="isLayerVisible('obstacle')">
      <circle
        v-for="obstacle in taskDetail.obstacles"
        :key="obstacle.id"
        :cx="project(obstacle.position).split(',')[0]"
        :cy="project(obstacle.position).split(',')[1]"
        r="1.4"
        class="obstacle"
      />
    </g>

    <polyline
      v-for="route in routes"
      :key="route.id"
      :points="pointsAttr(route.points)"
      :class="['route-line', routeClass(route)]"
    />

    <polyline
      v-for="(segmentPoints, index) in riskHighlightSegments"
      :key="`risk-highlight-${index}`"
      :points="pointsAttr(segmentPoints)"
      class="risk-highlight-line"
    />

    <polyline
      v-if="replannedRoute"
      :points="pointsAttr(replannedRoute.route.points)"
      class="route-line route-replanned"
    />

    <polyline
      v-if="referenceFlightTrail.length >= 2"
      :points="pointsAttr(referenceFlightTrail)"
      class="flight-trail flight-trail-reference"
    />

    <polyline
      v-if="actualFlightTrail.length >= 2"
      :points="pointsAttr(actualFlightTrail)"
      class="flight-trail flight-trail-actual-halo"
    />
    <polyline
      v-if="actualFlightTrail.length >= 2"
      :points="pointsAttr(actualFlightTrail)"
      class="flight-trail flight-trail-actual"
    />

    <g v-if="visionTiles.length">
      <polygon
        v-for="tile in visionTiles"
        :key="tile.tile_id"
        :points="pointsAttr(tile.bbox)"
        class="vision-tile"
      />
    </g>

    <g v-if="visionResult">
      <polygon
        v-for="candidate in visionResult.candidates"
        :key="candidate.tile_id"
        :points="pointsAttr(candidate.bbox)"
        :class="['vision-candidate-base', candidateClass(candidate)]"
      />
    </g>

    <circle
      :cx="project(selectedTask.start).split(',')[0]"
      :cy="project(selectedTask.start).split(',')[1]"
      r="1.8"
      class="start-point"
    />
    <circle
      :cx="project(selectedTask.target).split(',')[0]"
      :cy="project(selectedTask.target).split(',')[1]"
      r="1.8"
      class="target-point"
    />
    <circle
      v-if="currentPoint"
      :cx="project(currentPoint).split(',')[0]"
      :cy="project(currentPoint).split(',')[1]"
      r="1.5"
      class="uav-point"
    />
  </svg>
</template>

<style scoped>
.flight-trail {
  fill: none;
  stroke-linecap: round;
  stroke-linejoin: round;
  pointer-events: none;
}

.flight-trail-reference {
  stroke: rgba(255, 255, 255, 0.82);
  stroke-width: 0.75;
  stroke-dasharray: 2 1.2;
}

.flight-trail-actual-halo {
  stroke: rgba(0, 0, 0, 0.48);
  stroke-width: 2.2;
}

.flight-trail-actual {
  stroke: rgba(0, 224, 255, 0.95);
  stroke-width: 1.15;
}
</style>

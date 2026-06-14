<script setup>
import { computed, ref, watch } from "vue";

const props = defineProps({
  task: { type: Object, default: null },
  saving: { type: Boolean, default: false },
  error: { type: String, default: "" },
});

const emit = defineEmits(["save", "reload", "preview"]);

const draft = ref({ start: [0, 0, 120], target: [0, 0, 120] });
const dirty = ref(false);
const activePoint = ref("start");
const draggingPoint = ref("");
const mapRef = ref(null);

const validationMessage = computed(() => {
  const startMessage = validatePoint("起点", draft.value.start);
  if (startMessage) return startMessage;
  return validatePoint("终点", draft.value.target);
});

const mapBounds = computed(() => {
  const ring = props.task?.area?.coordinates?.[0] || [];
  const allPoints = [...ring, draft.value.start, draft.value.target].filter((point) => Array.isArray(point) && point.length >= 2);
  if (!allPoints.length) {
    return { minLon: 0, maxLon: 1, minLat: 0, maxLat: 1 };
  }
  const lons = allPoints.map((point) => point[0]);
  const lats = allPoints.map((point) => point[1]);
  const minLon = Math.min(...lons);
  const maxLon = Math.max(...lons);
  const minLat = Math.min(...lats);
  const maxLat = Math.max(...lats);
  const lonPad = Math.max((maxLon - minLon) * 0.08, 0.0006);
  const latPad = Math.max((maxLat - minLat) * 0.08, 0.0006);
  return {
    minLon: minLon - lonPad,
    maxLon: maxLon + lonPad,
    minLat: minLat - latPad,
    maxLat: maxLat + latPad,
  };
});

watch(
  () => props.task,
  (task) => {
    draft.value = cloneEndpoints(task);
    dirty.value = false;
    activePoint.value = "start";
  },
  { immediate: true, deep: true }
);

watch(
  draft,
  () => {
    if (!dirty.value) return;
    emit("preview", cloneDraft());
  },
  { deep: true }
);

function cloneEndpoints(task) {
  return {
    start: [...(task?.start || [0, 0, 120])],
    target: [...(task?.target || [0, 0, 120])],
  };
}

function cloneDraft() {
  return {
    start: draft.value.start.map(Number),
    target: draft.value.target.map(Number),
  };
}

function markDirty() {
  dirty.value = true;
}

function selectPoint(pointKey) {
  activePoint.value = pointKey;
}

function startDrag(pointKey, event) {
  draggingPoint.value = pointKey;
  activePoint.value = pointKey;
  event.currentTarget.setPointerCapture?.(event.pointerId);
}

function dragPoint(event) {
  if (!draggingPoint.value) return;
  const point = pointFromEvent(event);
  if (!point) return;
  const current = draft.value[draggingPoint.value];
  draft.value[draggingPoint.value] = [point[0], point[1], current[2]];
  markDirty();
}

function stopDrag() {
  draggingPoint.value = "";
}

function placeActivePoint(event) {
  if (draggingPoint.value) return;
  const point = pointFromEvent(event);
  if (!point) return;
  const current = draft.value[activePoint.value];
  draft.value[activePoint.value] = [point[0], point[1], current[2]];
  markDirty();
}

function updatePoint(pointKey, axis, value) {
  const next = [...draft.value[pointKey]];
  next[axis] = Number(value);
  draft.value[pointKey] = next;
  markDirty();
}

function nudgeActive(direction) {
  const box = mapBounds.value;
  const stepLon = (box.maxLon - box.minLon) * 0.012;
  const stepLat = (box.maxLat - box.minLat) * 0.012;
  const [lon, lat, altitude] = draft.value[activePoint.value];
  const delta = {
    up: [0, stepLat],
    down: [0, -stepLat],
    left: [-stepLon, 0],
    right: [stepLon, 0],
  }[direction];
  if (!delta) return;
  draft.value[activePoint.value] = [roundCoord(lon + delta[0]), roundCoord(lat + delta[1]), altitude];
  markDirty();
}

function saveEndpoints() {
  if (validationMessage.value) return;
  emit("save", cloneDraft());
}

function reloadEndpoints() {
  emit("reload");
}

function validatePoint(label, point) {
  if (!Array.isArray(point) || point.length !== 3) return `${label}需要经度、纬度和高度。`;
  if (point.some((value) => !Number.isFinite(Number(value)))) return `${label}坐标必须是有效数字。`;
  if (point[2] < 0) return `${label}高度不能小于 0 米。`;
  return "";
}

function project(point) {
  const box = mapBounds.value;
  const x = ((point[0] - box.minLon) / (box.maxLon - box.minLon || 1)) * 100;
  const y = (1 - (point[1] - box.minLat) / (box.maxLat - box.minLat || 1)) * 100;
  return [x, y];
}

function unproject([x, y]) {
  const box = mapBounds.value;
  const lon = box.minLon + (x / 100) * (box.maxLon - box.minLon);
  const lat = box.minLat + ((100 - y) / 100) * (box.maxLat - box.minLat);
  return [roundCoord(lon), roundCoord(lat)];
}

function pointFromEvent(event) {
  const rect = mapRef.value?.getBoundingClientRect();
  if (!rect) return null;
  const x = ((event.clientX - rect.left) / rect.width) * 100;
  const y = ((event.clientY - rect.top) / rect.height) * 100;
  return unproject([clamp(x, 0, 100), clamp(y, 0, 100)]);
}

function pointsAttr(points) {
  return (points || []).map((point) => project(point).join(",")).join(" ");
}

function formatCoord(value) {
  return Number(value || 0).toFixed(6);
}

function roundCoord(value) {
  return Number(value.toFixed(7));
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}
</script>

<template>
  <section class="glass-panel endpoint-editor">
    <div class="panel-title-row">
      <h2>起终点编辑</h2>
      <span>{{ dirty ? "未保存" : "已同步" }}</span>
    </div>

    <div class="endpoint-switch">
      <button :class="{ active: activePoint === 'start' }" type="button" @click="selectPoint('start')">起点</button>
      <button :class="{ active: activePoint === 'target' }" type="button" @click="selectPoint('target')">终点</button>
    </div>

    <div class="endpoint-map-editor">
      <svg
        ref="mapRef"
        viewBox="0 0 100 100"
        role="img"
        aria-label="起终点交互编辑图"
        @pointerdown="placeActivePoint"
        @pointermove="dragPoint"
        @pointerup="stopDrag"
        @pointerleave="stopDrag"
      >
        <rect class="risk-map-bg" x="0" y="0" width="100" height="100" />
        <polygon
          v-if="task?.area?.coordinates?.[0]"
          class="risk-map-task-area"
          :points="pointsAttr(task.area.coordinates[0])"
        />
        <polyline class="endpoint-preview-line" :points="pointsAttr([draft.start, draft.target])" />
        <g
          v-for="pointKey in ['start', 'target']"
          :key="pointKey"
          :class="['endpoint-marker', pointKey, activePoint === pointKey ? 'active' : '']"
          :transform="`translate(${project(draft[pointKey])[0]} ${project(draft[pointKey])[1]})`"
          @pointerdown.stop="startDrag(pointKey, $event)"
        >
          <circle r="3.6" />
          <text x="5" y="-5">{{ pointKey === "start" ? "起" : "终" }}</text>
        </g>
      </svg>
      <small>点击地图移动当前选中的点，拖动标记可连续调整。</small>
    </div>

    <div class="endpoint-coordinate-grid">
      <label v-for="pointKey in ['start', 'target']" :key="pointKey">
        <strong>{{ pointKey === "start" ? "起点" : "终点" }}</strong>
        <span>经度</span>
        <input :value="formatCoord(draft[pointKey][0])" type="number" step="0.000001" @input="updatePoint(pointKey, 0, $event.target.value)" />
        <span>纬度</span>
        <input :value="formatCoord(draft[pointKey][1])" type="number" step="0.000001" @input="updatePoint(pointKey, 1, $event.target.value)" />
        <span>高度</span>
        <input :value="draft[pointKey][2]" type="number" step="1" min="0" @input="updatePoint(pointKey, 2, $event.target.value)" />
      </label>
    </div>

    <div class="endpoint-nudge-grid">
      <button type="button" @click="nudgeActive('up')">上移</button>
      <button type="button" @click="nudgeActive('down')">下移</button>
      <button type="button" @click="nudgeActive('left')">左移</button>
      <button type="button" @click="nudgeActive('right')">右移</button>
    </div>

    <div class="risk-editor-actions">
      <button type="button" :disabled="saving || Boolean(validationMessage)" @click="saveEndpoints">保存</button>
      <button type="button" :disabled="saving" @click="reloadEndpoints">重载</button>
    </div>

    <p v-if="validationMessage || error" class="risk-editor-message">
      {{ validationMessage || error }}
    </p>
  </section>
</template>

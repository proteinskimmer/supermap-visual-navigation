<script setup>
import { computed, ref, watch } from "vue";

const props = defineProps({
  task: { type: Object, default: null },
  zones: { type: Array, default: () => [] },
  saving: { type: Boolean, default: false },
  error: { type: String, default: "" },
});

const emit = defineEmits(["save", "reload", "preview"]);

const draftZones = ref([]);
const selectedId = ref("");
const dirty = ref(false);
const dragVertexIndex = ref(null);
const selectedVertexIndex = ref(null);
const mapRef = ref(null);

const selectedZone = computed(() => draftZones.value.find((zone) => zone.id === selectedId.value) || draftZones.value[0] || null);
const validationMessage = computed(() => validateZones(draftZones.value));
const selectedEditablePoints = computed(() => selectedZone.value?.polygon?.slice(0, -1) || []);

const mapBounds = computed(() => {
  const ring = props.task?.area?.coordinates?.[0] || [];
  const zonePoints = draftZones.value.flatMap((zone) => zone.polygon || []);
  const allPoints = [...ring, ...zonePoints].filter((point) => Array.isArray(point) && point.length >= 2);
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
  () => props.zones,
  (zones) => {
    draftZones.value = cloneZones(zones);
    selectedId.value = zones[0]?.id || "";
    selectedVertexIndex.value = null;
    dirty.value = false;
  },
  { immediate: true, deep: true }
);

watch(
  draftZones,
  () => {
    emit("preview", cloneZones(draftZones.value));
  },
  { deep: true }
);

function cloneZones(zones) {
  return JSON.parse(JSON.stringify(zones || []));
}

function markDirty() {
  dirty.value = true;
}

function taskCenter() {
  const ring = props.task?.area?.coordinates?.[0] || [];
  const usable = ring.slice(0, ring.length > 1 ? -1 : ring.length);
  if (!usable.length) return [116.16, 39.16];
  const total = usable.reduce(
    (acc, point) => {
      acc.lon += point[0];
      acc.lat += point[1];
      return acc;
    },
    { lon: 0, lat: 0 }
  );
  return [total.lon / usable.length, total.lat / usable.length];
}

function addZone() {
  const [lon, lat] = taskCenter();
  const index = draftZones.value.length + 1;
  const size = 0.0012;
  const zone = {
    id: `risk_custom_${Date.now()}`,
    name: `自定义风险区 ${index}`,
    type: "custom",
    level: 3,
    buffer_m: 80,
    active: true,
    polygon: [
      [roundCoord(lon - size), roundCoord(lat - size)],
      [roundCoord(lon + size), roundCoord(lat - size)],
      [roundCoord(lon + size), roundCoord(lat + size)],
      [roundCoord(lon - size), roundCoord(lat + size)],
      [roundCoord(lon - size), roundCoord(lat - size)],
    ],
  };
  draftZones.value = [...draftZones.value, zone];
  selectedId.value = zone.id;
  selectedVertexIndex.value = null;
  markDirty();
}

function deleteSelectedZone() {
  if (!selectedZone.value) return;
  draftZones.value = draftZones.value.filter((zone) => zone.id !== selectedZone.value.id);
  selectedId.value = draftZones.value[0]?.id || "";
  selectedVertexIndex.value = null;
  markDirty();
}

function duplicateSelectedZone() {
  if (!selectedZone.value) return;
  const source = cloneZones([selectedZone.value])[0];
  source.id = `risk_custom_${Date.now()}`;
  source.name = `${source.name} 副本`;
  source.polygon = source.polygon.map(([lon, lat]) => [roundCoord(lon + 0.0004), roundCoord(lat + 0.0004)]);
  closePolygon(source);
  draftZones.value = [...draftZones.value, source];
  selectedId.value = source.id;
  selectedVertexIndex.value = null;
  markDirty();
}

function selectZone(zoneId) {
  selectedId.value = zoneId;
  selectedVertexIndex.value = null;
}

function addPointAtMapEvent(event) {
  if (!selectedZone.value || dragVertexIndex.value !== null) return;
  const point = pointFromEvent(event);
  if (!point) return;
  const polygon = selectedZone.value.polygon;
  const insertIndex = nearestSegmentIndex(point, polygon);
  polygon.splice(insertIndex + 1, 0, point);
  closePolygon(selectedZone.value);
  selectedVertexIndex.value = insertIndex + 1;
  markDirty();
}

function deleteSelectedPoint() {
  if (!selectedZone.value || selectedVertexIndex.value === null) return;
  deletePoint(selectedVertexIndex.value);
}

function deletePoint(index) {
  if (!selectedZone.value || selectedZone.value.polygon.length <= 4) return;
  selectedZone.value.polygon.splice(index, 1);
  closePolygon(selectedZone.value);
  selectedVertexIndex.value = Math.min(index, selectedZone.value.polygon.length - 2);
  markDirty();
}

function startDragVertex(index, event) {
  if (!selectedZone.value) return;
  dragVertexIndex.value = index;
  selectedVertexIndex.value = index;
  event.currentTarget.setPointerCapture?.(event.pointerId);
}

function dragVertex(event) {
  if (dragVertexIndex.value === null || !selectedZone.value) return;
  const point = pointFromEvent(event);
  if (!point) return;
  selectedZone.value.polygon[dragVertexIndex.value] = point;
  closePolygon(selectedZone.value);
  markDirty();
}

function stopDragVertex() {
  dragVertexIndex.value = null;
}

function moveSelectedZone(deltaLon, deltaLat) {
  if (!selectedZone.value) return;
  selectedZone.value.polygon = selectedZone.value.polygon.map(([lon, lat]) => [roundCoord(lon + deltaLon), roundCoord(lat + deltaLat)]);
  closePolygon(selectedZone.value);
  markDirty();
}

function nudgeSelectedZone(direction) {
  const box = mapBounds.value;
  const stepLon = (box.maxLon - box.minLon) * 0.015;
  const stepLat = (box.maxLat - box.minLat) * 0.015;
  if (direction === "up") moveSelectedZone(0, stepLat);
  if (direction === "down") moveSelectedZone(0, -stepLat);
  if (direction === "left") moveSelectedZone(-stepLon, 0);
  if (direction === "right") moveSelectedZone(stepLon, 0);
}

function updateCoordinate(point, axis, value) {
  point[axis] = Number(value);
  closePolygon(selectedZone.value);
  markDirty();
}

function closePolygon(zone) {
  if (!zone?.polygon?.length) return;
  const first = zone.polygon[0];
  const last = zone.polygon[zone.polygon.length - 1];
  if (zone.polygon.length === 1) {
    zone.polygon.push([...first]);
    return;
  }
  last[0] = first[0];
  last[1] = first[1];
}

function saveZones() {
  const message = validationMessage.value;
  if (message) return;
  emit("save", cloneZones(draftZones.value));
}

function reloadZones() {
  emit("reload");
}

function validateZones(zones) {
  const ids = zones.map((zone) => zone.id.trim()).filter(Boolean);
  if (ids.length !== zones.length) return "风险区编号不能为空。";
  if (new Set(ids).size !== ids.length) return "风险区编号不能重复。";
  for (const zone of zones) {
    if (!zone.name.trim()) return `${zone.id} 名称不能为空。`;
    if (!zone.polygon || zone.polygon.length < 4) return `${zone.id} 至少需要 3 个有效顶点。`;
    const first = zone.polygon[0];
    const last = zone.polygon[zone.polygon.length - 1];
    if (!first || !last || first[0] !== last[0] || first[1] !== last[1]) return `${zone.id} 多边形必须首尾闭合。`;
  }
  return "";
}

function project(point) {
  const box = mapBounds.value;
  const x = ((point[0] - box.minLon) / (box.maxLon - box.minLon || 1)) * 100;
  const y = (1 - (point[1] - box.minLat) / (box.maxLat - box.minLat || 1)) * 100;
  return [x, y];
}

function pointsAttr(points) {
  return (points || []).map((point) => project(point).join(",")).join(" ");
}

function pointFromEvent(event) {
  const rect = mapRef.value?.getBoundingClientRect();
  if (!rect) return null;
  const x = ((event.clientX - rect.left) / rect.width) * 100;
  const y = ((event.clientY - rect.top) / rect.height) * 100;
  return unproject([clamp(x, 0, 100), clamp(y, 0, 100)]);
}

function unproject([x, y]) {
  const box = mapBounds.value;
  return [
    roundCoord(box.minLon + (x / 100) * (box.maxLon - box.minLon)),
    roundCoord(box.minLat + ((100 - y) / 100) * (box.maxLat - box.minLat)),
  ];
}

function nearestSegmentIndex(point, polygon) {
  const editable = polygon.slice(0, -1);
  if (editable.length < 2) return Math.max(0, editable.length - 1);
  const p = project(point);
  let bestIndex = 0;
  let bestDistance = Number.POSITIVE_INFINITY;
  for (let index = 0; index < editable.length; index += 1) {
    const a = project(editable[index]);
    const b = project(editable[(index + 1) % editable.length]);
    const distance = distanceToSegment(p, a, b);
    if (distance < bestDistance) {
      bestDistance = distance;
      bestIndex = index;
    }
  }
  return bestIndex;
}

function distanceToSegment(point, start, end) {
  const dx = end[0] - start[0];
  const dy = end[1] - start[1];
  if (dx === 0 && dy === 0) return Math.hypot(point[0] - start[0], point[1] - start[1]);
  const t = clamp(((point[0] - start[0]) * dx + (point[1] - start[1]) * dy) / (dx * dx + dy * dy), 0, 1);
  return Math.hypot(point[0] - (start[0] + t * dx), point[1] - (start[1] + t * dy));
}

function zoneClass(zone) {
  if (zone.id === selectedZone.value?.id) return "risk-sketch-selected";
  if (zone.level >= 5) return "risk-sketch-critical";
  if (zone.level >= 4) return "risk-sketch-high";
  return "risk-sketch-muted";
}

function roundCoord(value) {
  return Number(Number(value).toFixed(6));
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}
</script>

<template>
  <section class="glass-panel risk-editor">
    <div class="panel-title-row">
      <h2>风险区编辑</h2>
      <span>{{ draftZones.length }} 个{{ dirty ? " / 未保存" : "" }}</span>
    </div>

    <div class="risk-editor-actions">
      <button type="button" @click="addZone">新增</button>
      <button type="button" :disabled="!selectedZone" @click="duplicateSelectedZone">复制</button>
      <button type="button" :disabled="!selectedZone" @click="deleteSelectedZone">删除</button>
      <button type="button" :disabled="saving" @click="reloadZones">重载</button>
      <button type="button" class="risk-save-button" :disabled="saving || Boolean(validationMessage)" @click="saveZones">
        {{ saving ? "保存中" : "保存" }}
      </button>
    </div>

    <select v-if="draftZones.length" v-model="selectedId" class="risk-select">
      <option v-for="zone in draftZones" :key="zone.id" :value="zone.id">
        {{ zone.name }} / L{{ zone.level }}
      </option>
    </select>

    <div class="risk-map-editor">
      <svg
        ref="mapRef"
        viewBox="0 0 100 100"
        role="img"
        aria-label="风险区交互编辑图"
        @click="addPointAtMapEvent"
        @pointermove="dragVertex"
        @pointerup="stopDragVertex"
        @pointerleave="stopDragVertex"
      >
        <defs>
          <pattern id="risk-editor-grid" width="10" height="10" patternUnits="userSpaceOnUse">
            <path d="M 10 0 L 0 0 0 10" fill="none" stroke="rgba(82, 116, 143, 0.14)" stroke-width="0.28" />
          </pattern>
        </defs>
        <rect width="100" height="100" class="risk-map-bg" />
        <rect width="100" height="100" fill="url(#risk-editor-grid)" />
        <polygon v-if="task?.area?.coordinates?.[0]" :points="pointsAttr(task.area.coordinates[0])" class="risk-map-task-area" />
        <polygon
          v-for="zone in draftZones"
          :key="zone.id"
          :points="pointsAttr(zone.polygon)"
          :class="['risk-sketch-zone', zoneClass(zone)]"
          @click.stop="selectZone(zone.id)"
        />
        <g v-if="selectedZone">
          <polyline :points="pointsAttr(selectedZone.polygon)" class="risk-sketch-outline" />
          <circle
            v-for="(point, index) in selectedEditablePoints"
            :key="`${selectedZone.id}-${index}`"
            :cx="project(point)[0]"
            :cy="project(point)[1]"
            :class="['risk-vertex', selectedVertexIndex === index ? 'active' : '']"
            r="2.5"
            @click.stop="selectedVertexIndex = index"
            @pointerdown.stop="startDragVertex(index, $event)"
          />
        </g>
      </svg>
      <div class="risk-map-tools">
        <span>拖动圆点调整边界，点击图面插入顶点。</span>
        <button type="button" :disabled="selectedVertexIndex === null" @click="deleteSelectedPoint">删点</button>
      </div>
    </div>

    <div v-if="selectedZone" class="risk-nudge-grid" aria-label="微调风险区位置">
      <button type="button" @click="nudgeSelectedZone('up')">上移</button>
      <button type="button" @click="nudgeSelectedZone('left')">左移</button>
      <button type="button" @click="nudgeSelectedZone('right')">右移</button>
      <button type="button" @click="nudgeSelectedZone('down')">下移</button>
    </div>

    <div v-if="selectedZone" class="risk-form">
      <label>
        <span>编号</span>
        <input v-model.trim="selectedZone.id" type="text" @input="markDirty" />
      </label>
      <label>
        <span>名称</span>
        <input v-model.trim="selectedZone.name" type="text" @input="markDirty" />
      </label>
      <label>
        <span>类型</span>
        <select v-model="selectedZone.type" @change="markDirty">
          <option value="fire">山火</option>
          <option value="landslide">塌方</option>
          <option value="no_fly">禁飞</option>
          <option value="custom">自定义</option>
        </select>
      </label>
      <label>
        <span>等级</span>
        <input v-model.number="selectedZone.level" min="1" max="5" type="number" @input="markDirty" />
      </label>
      <label>
        <span>缓冲</span>
        <input v-model.number="selectedZone.buffer_m" min="0" step="5" type="number" @input="markDirty" />
      </label>
      <label class="risk-check">
        <input v-model="selectedZone.active" type="checkbox" @change="markDirty" />
        <span>启用</span>
      </label>
    </div>

    <details v-if="selectedZone" class="risk-coordinate-details">
      <summary>坐标明细</summary>
      <div v-for="(point, index) in selectedZone.polygon" :key="index" class="risk-point-row">
        <span>{{ index + 1 }}</span>
        <input
          :value="point[0]"
          :disabled="index === selectedZone.polygon.length - 1"
          type="number"
          step="0.0001"
          @input="updateCoordinate(point, 0, $event.target.value)"
        />
        <input
          :value="point[1]"
          :disabled="index === selectedZone.polygon.length - 1"
          type="number"
          step="0.0001"
          @input="updateCoordinate(point, 1, $event.target.value)"
        />
        <button type="button" :disabled="index === selectedZone.polygon.length - 1 || selectedZone.polygon.length <= 4" @click="deletePoint(index)">
          -
        </button>
      </div>
    </details>

    <p v-if="validationMessage || error" class="risk-editor-message">{{ validationMessage || error }}</p>
    <p v-else class="summary-text">编辑会实时预览到主场景，保存后重新计算当前航线风险。</p>
  </section>
</template>

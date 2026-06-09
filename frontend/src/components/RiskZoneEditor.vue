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

const selectedZone = computed(() => draftZones.value.find((zone) => zone.id === selectedId.value) || draftZones.value[0] || null);
const validationMessage = computed(() => validateZones(draftZones.value));

watch(
  () => props.zones,
  (zones) => {
    draftZones.value = cloneZones(zones);
    selectedId.value = zones[0]?.id || "";
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
  const size = 0.006;
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
  markDirty();
}

function deleteSelectedZone() {
  if (!selectedZone.value) return;
  draftZones.value = draftZones.value.filter((zone) => zone.id !== selectedZone.value.id);
  selectedId.value = draftZones.value[0]?.id || "";
  markDirty();
}

function addPoint() {
  if (!selectedZone.value) return;
  const polygon = selectedZone.value.polygon;
  const anchor = polygon[Math.max(0, polygon.length - 2)] || polygon[0] || taskCenter();
  polygon.splice(Math.max(0, polygon.length - 1), 0, [roundCoord(anchor[0] + 0.002), roundCoord(anchor[1] + 0.002)]);
  closePolygon(selectedZone.value);
  markDirty();
}

function deletePoint(index) {
  if (!selectedZone.value || selectedZone.value.polygon.length <= 4) return;
  selectedZone.value.polygon.splice(index, 1);
  closePolygon(selectedZone.value);
  markDirty();
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
  if (first !== last) {
    last[0] = first[0];
    last[1] = first[1];
  }
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
    if (!zone.polygon || zone.polygon.length < 4) return `${zone.id} 至少需要 4 个坐标点。`;
    const first = zone.polygon[0];
    const last = zone.polygon[zone.polygon.length - 1];
    if (!first || !last || first[0] !== last[0] || first[1] !== last[1]) return `${zone.id} 多边形必须首尾闭合。`;
  }
  return "";
}

function roundCoord(value) {
  return Number(value.toFixed(6));
}
</script>

<template>
  <section class="glass-panel risk-editor">
    <div class="panel-title-row">
      <h2>风险区编辑</h2>
      <span>{{ draftZones.length }} 个{{ dirty ? " · 未保存" : "" }}</span>
    </div>

    <div class="risk-editor-actions">
      <button type="button" @click="addZone">新增</button>
      <button type="button" :disabled="!selectedZone" @click="deleteSelectedZone">删除</button>
      <button type="button" :disabled="saving" @click="reloadZones">重载</button>
      <button type="button" :disabled="saving || Boolean(validationMessage)" @click="saveZones">
        {{ saving ? "保存中" : "保存" }}
      </button>
    </div>

    <select v-if="draftZones.length" v-model="selectedId" class="risk-select">
      <option v-for="zone in draftZones" :key="zone.id" :value="zone.id">
        {{ zone.name }} · L{{ zone.level }}
      </option>
    </select>

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

    <div v-if="selectedZone" class="risk-points">
      <div class="risk-points-head">
        <strong>多边形坐标</strong>
        <button type="button" @click="addPoint">加点</button>
      </div>
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
    </div>

    <p v-if="validationMessage || error" class="risk-editor-message">{{ validationMessage || error }}</p>
    <p v-else class="summary-text">保存后会刷新任务详情，并重新计算当前候选航线风险。</p>
  </section>
</template>

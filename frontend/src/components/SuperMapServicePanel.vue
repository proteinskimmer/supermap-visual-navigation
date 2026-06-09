<script setup>
import { computed } from "vue";

const props = defineProps({
  config: { type: Object, default: null },
  status: { type: Object, default: null },
  refreshing: { type: Boolean, default: false },
});

defineEmits(["refresh"]);

const services = computed(() => {
  const raw = props.config?.services || {};
  const runtime = props.status?.services || {};
  return ["scene", "map", "data"].map((id) => ({
    id,
    name: raw[id]?.name || "-",
    status: raw[id]?.status || "missing",
    runtimeStatus: runtime[id]?.runtime_status || "not_checked",
    reachable: runtime[id]?.reachable,
    url: raw[id]?.resource_url || raw[id]?.url || "",
    checkedUrl: runtime[id]?.checked_url || "",
    httpStatus: runtime[id]?.http_status || "-",
    message: runtime[id]?.message || "",
  }));
});

const datasets = computed(() =>
  props.status?.layers?.length
    ? props.status.layers
    : Object.entries(props.config?.layers || {}).map(([id, layer]) => ({
        id,
        dataset: layer.dataset,
        geometry: layer.geometry,
        accessible: null,
        runtime_status: "not_checked",
      }))
);

function statusClass(status) {
  if (status === "verified") return "service-ok";
  if (status === "optional") return "service-muted";
  return "service-warn";
}

function serviceLabel(id) {
  if (id === "scene") return "三维";
  if (id === "map") return "地图";
  return "数据";
}

const mapMeta = computed(() => props.status?.map || {});
const dataMeta = computed(() => props.status?.data || {});

function runtimeLabel(status) {
  if (status === "verified") return "已验证";
  if (status === "optional") return "可选";
  if (status === "missing") return "缺失";
  if (status === "not_checked") return "未检测";
  return status || "未知";
}
</script>

<template>
  <section class="panel-section">
    <div class="panel-title-row">
      <h2>SuperMap 服务</h2>
      <button class="icon-action" :disabled="refreshing" title="重新检测 SuperMap 服务" @click="$emit('refresh')">
        {{ refreshing ? "..." : "↻" }}
      </button>
    </div>

    <div v-if="!config" class="service-panel service-muted">
      <strong>配置加载中</strong>
      <small>/api/supermap/config</small>
    </div>

    <div v-else class="service-panel">
      <div class="service-meta">
        <span>iServer</span>
        <strong>{{ config.iserver?.version || "-" }}</strong>
      </div>
      <div class="service-meta">
        <span>工作空间</span>
        <strong>{{ config.iserver?.coordinate_system || "-" }}</strong>
      </div>
      <div class="service-meta">
        <span>接口门禁</span>
        <strong>{{ status?.all_expected_layers_accessible ? "8 个图层已验证" : "检测中" }}</strong>
      </div>
      <div class="service-meta">
        <span>检测时间</span>
        <strong>{{ status?.generated_at || "-" }}</strong>
      </div>

      <div class="service-kpis">
        <span>
          <small>地图图层</small>
          <strong>{{ mapMeta.layer_count ?? "-" }}</strong>
        </span>
        <span>
          <small>EPSG</small>
          <strong>{{ mapMeta.epsg || "-" }}</strong>
        </span>
        <span>
          <small>数据集</small>
          <strong>{{ dataMeta.dataset_count ?? "-" }}</strong>
        </span>
      </div>

      <div class="service-list">
        <article
          v-for="service in services"
          :key="service.id"
          :class="['service-row', statusClass(service.runtimeStatus === 'verified' ? 'verified' : service.status)]"
        >
          <span>{{ serviceLabel(service.id) }}</span>
          <strong>{{ runtimeLabel(service.runtimeStatus) }}</strong>
          <small>{{ service.name }}</small>
          <small>HTTP {{ service.httpStatus }} · {{ service.message || "未检测" }}</small>
          <small>{{ service.checkedUrl || service.url }}</small>
        </article>
      </div>

      <div class="service-datasets">
        <span>{{ datasets.length }} 个业务图层</span>
        <small v-for="dataset in datasets" :key="dataset.id">
          {{ dataset.dataset }} / {{ dataset.geometry }} / {{ runtimeLabel(dataset.runtime_status) }}
        </small>
      </div>
    </div>
  </section>
</template>

<script setup>
import EmptyState from "./EmptyState.vue";

defineProps({
  tasks: { type: Array, default: () => [] },
  layers: { type: Array, default: () => [] },
  visionImages: { type: Array, default: () => [] },
  selectedVisionImageId: { type: String, default: "" },
  selectedTask: { type: Object, default: null },
  selectedRoute: { type: Object, default: null },
  simulation: { type: Object, default: null },
  canTriggerReplan: { type: Boolean, default: false },
  isPlaying: { type: Boolean, default: false },
  demoSteps: { type: Array, default: () => [] },
});

defineEmits([
  "plan-routes",
  "start-simulation",
  "advance-simulation",
  "toggle-play",
  "trigger-replan",
  "reset-simulation",
  "open-report",
  "select-vision-image",
]);
</script>

<template>
  <aside class="side-panel">
    <section class="panel-section">
      <h2>任务</h2>
      <EmptyState v-if="!tasks.length" title="任务未加载" message="等待后端返回任务列表。" />
      <button v-for="task in tasks" v-else :key="task.id" class="task-button active">
        <span>{{ task.display_name }}</span>
        <small>{{ task.id }}</small>
      </button>
    </section>

    <section class="panel-section">
      <h2>图层</h2>
      <EmptyState v-if="!layers.length" title="图层未加载" message="等待图层配置或 iServer 服务地址。" />
      <label v-for="layer in layers" v-else :key="layer.id" class="toggle-row">
        <input v-model="layer.visible" type="checkbox" />
        <span>{{ layer.name }}</span>
      </label>
    </section>

    <section class="panel-section">
      <h2>视觉样例</h2>
      <EmptyState v-if="!visionImages.length" title="样例未加载" message="视觉模块可后置，当前不影响主流程。" />
      <button
        v-for="image in visionImages"
        v-else
        :key="image.id"
        :class="['task-button', selectedVisionImageId === image.id ? 'active' : '']"
        @click="$emit('select-vision-image', image.id)"
      >
        <span>{{ image.name }}</span>
        <small>{{ image.id }} · {{ image.capture_time_s }}s</small>
      </button>
    </section>

    <section class="panel-section">
      <h2>控制</h2>
      <div class="button-grid">
        <button :disabled="!selectedTask" @click="$emit('plan-routes')">规划</button>
        <button :disabled="!selectedRoute" @click="$emit('start-simulation')">仿真</button>
        <button :disabled="!simulation" @click="$emit('advance-simulation')">推进</button>
        <button :disabled="!selectedRoute" @click="$emit('toggle-play')">{{ isPlaying ? "暂停" : "播放" }}</button>
        <button :disabled="!canTriggerReplan" @click="$emit('trigger-replan')">重规划</button>
        <button @click="$emit('reset-simulation')">重置</button>
        <button :disabled="!selectedTask" @click="$emit('open-report')">报告</button>
      </div>
    </section>

    <section class="panel-section">
      <h2>演示闭环</h2>
      <ol class="demo-checklist">
        <li v-for="step in demoSteps" :key="step.label" :class="{ done: step.done }">
          <span></span>
          {{ step.label }}
        </li>
      </ol>
    </section>
  </aside>
</template>

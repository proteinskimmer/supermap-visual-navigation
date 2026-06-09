<script setup>
import EmptyState from "./EmptyState.vue";

defineProps({
  progress: { type: Number, default: 0 },
  events: { type: Array, default: () => [] },
});
</script>

<template>
  <footer class="timeline">
    <div class="progress-track">
      <span :style="{ width: `${progress}%` }"></span>
    </div>
    <div v-if="events.length" class="event-log">
      <article v-for="event in events" :key="`${event.type}-${event.time_s}`">
        <strong>{{ event.time_s }}秒</strong>
        <span>{{ event.title }}</span>
        <small>{{ event.description }}</small>
      </article>
    </div>
    <EmptyState v-else title="仿真未开始" message="点击仿真后显示时间轴事件日志。" />
  </footer>
</template>

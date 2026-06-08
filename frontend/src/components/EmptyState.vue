<template>
  <div class="empty-state">
    <strong>{{ title }}</strong>
    <span>{{ message }}</span>
  </div>
</template>

<script setup>
defineProps({
  title: { type: String, default: "暂无数据" },
  message: { type: String, default: "等待数据加载或执行相关操作。" },
});
</script>

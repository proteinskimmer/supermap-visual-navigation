<script setup>
import ElevationProfile from "./ElevationProfile.vue";
import EmptyState from "./EmptyState.vue";

defineProps({
  report: { type: Object, default: null },
  riskAnalysis: { type: Object, default: null },
  events: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  error: { type: String, default: "" },
});

defineEmits(["close", "reload"]);
</script>

<template>
  <main class="app-shell report-page">
    <header class="topbar">
      <div>
        <p class="eyebrow">Mission Report</p>
        <h1>任务报告</h1>
      </div>
      <div class="report-actions">
        <button @click="$emit('reload')">刷新</button>
        <button @click="$emit('close')">返回工作台</button>
      </div>
    </header>

    <section v-if="error" class="banner">{{ error }}</section>

    <section class="report-layout">
      <EmptyState v-if="loading" title="报告生成中" message="正在汇总航线、风险、事件和视觉匹配结果。" />
      <EmptyState v-else-if="!report" title="暂无报告" message="返回工作台后点击报告生成任务摘要。" />

      <template v-else>
        <section class="report-hero">
          <div>
            <span>任务</span>
            <strong>{{ report.task.display_name }}</strong>
          </div>
          <div>
            <span>推荐航线</span>
            <strong>{{ report.recommended_route.name }}</strong>
          </div>
          <div>
            <span>风险评分</span>
            <strong>{{ report.risk.score }}</strong>
          </div>
          <div>
            <span>事件数量</span>
            <strong>{{ events.length || report.events.length }}</strong>
          </div>
        </section>

        <section class="report-section">
          <h2>摘要</h2>
          <p class="summary-text">{{ report.summary }}</p>
        </section>

        <section class="report-section">
          <h2>航线</h2>
          <div class="report-grid report-grid-wide">
            <span>模式</span>
            <strong>{{ report.recommended_route.mode }}</strong>
            <span>距离</span>
            <strong>{{ report.recommended_route.distance_m }} m</strong>
            <span>预计时间</span>
            <strong>{{ report.recommended_route.estimated_time_s }} s</strong>
            <span>转弯数</span>
            <strong>{{ report.recommended_route.turn_count }}</strong>
          </div>
        </section>

        <section class="report-section">
          <h2>风险原因</h2>
          <ul class="risk-list">
            <li v-for="segment in report.risk.segments" :key="segment.segment_id">
              {{ segment.reason }}（{{ segment.risk_level }}，-{{ segment.deduct_score }}）
            </li>
            <li v-if="!report.risk.segments.length">当前报告未记录高风险航段</li>
          </ul>
        </section>

        <ElevationProfile :profile="riskAnalysis?.profile || report.risk.profile || []" />

        <section class="report-section">
          <h2>事件日志</h2>
          <div class="event-log report-event-log">
            <article v-for="event in events.length ? events : report.events" :key="`${event.type}-${event.time_s}`">
              <strong>{{ event.time_s }}s</strong>
              <span>{{ event.title }}</span>
              <small>{{ event.description }}</small>
            </article>
          </div>
        </section>

        <section class="report-section">
          <h2>视觉匹配</h2>
          <div class="candidate-row" v-for="candidate in report.vision.candidates" :key="candidate.tile_id">
            <span>{{ candidate.tile_id }}</span>
            <strong>{{ Math.round(candidate.confidence * 100) }}%</strong>
            <small>{{ candidate.matched_points }} pts</small>
            <em>{{ candidate.reason }}</em>
          </div>
        </section>
      </template>
    </section>
  </main>
</template>

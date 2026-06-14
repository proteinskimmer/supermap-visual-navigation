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

function routeModeLabel(mode) {
  if (mode === "shortest") return "最短航线";
  if (mode === "safest") return "安全优先";
  if (mode === "balanced") return "综合平衡";
  return mode || "-";
}

function qualityGradeLabel(grade) {
  if (grade === "navigation_verified") return "导航级通过";
  if (grade === "demo_verified") return "演示级通过";
  if (grade === "review_required") return "需要复核";
  return grade || "-";
}

function percent(value) {
  return `${Math.round((value || 0) * 100)}%`;
}

function countMapText(counts) {
  if (!counts) return "-";
  const entries = Object.entries(counts);
  if (!entries.length) return "-";
  return entries.map(([key, value]) => `${key}: ${value}`).join(" / ");
}
</script>

<template>
  <main class="app-shell report-page">
    <header class="topbar">
      <div>
        <p class="eyebrow">任务摘要</p>
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

        <section class="report-section" v-if="report.navigation_quality">
          <h2>视觉导航质量</h2>
          <div class="report-grid report-grid-wide">
            <span>Matcher</span>
            <strong>{{ report.navigation_quality.matcher_mode }}</strong>
            <span>质量等级</span>
            <strong>{{ qualityGradeLabel(report.navigation_quality.quality_grade) }}</strong>
            <span>视觉观测帧</span>
            <strong>{{ report.navigation_quality.visual_observation_count }} / {{ report.navigation_quality.frame_count }}</strong>
            <span>平均置信度</span>
            <strong>{{ percent(report.navigation_quality.confidence?.average) }}</strong>
            <span>平均误差半径</span>
            <strong>{{ report.navigation_quality.visual_error?.average_error_radius_m }} 米</strong>
            <span>融合平均偏差</span>
            <strong>{{ report.navigation_quality.fused_trajectory?.average_deviation_m }} 米</strong>
            <span>终点误差</span>
            <strong>{{ report.navigation_quality.fused_trajectory?.final_error_m }} 米</strong>
            <span>最大步速</span>
            <strong>{{ report.navigation_quality.fused_trajectory?.max_step_mps }} m/s</strong>
            <span>平滑性</span>
            <strong>{{ report.navigation_quality.fused_trajectory?.smoothness_passed ? "通过" : "需复核" }}</strong>
            <span>回退帧</span>
            <strong>{{ report.navigation_quality.fallback_count }}</strong>
            <span>Provider</span>
            <strong>{{ countMapText(report.navigation_quality.provider_counts) }}</strong>
          </div>
          <p class="summary-text">{{ report.navigation_quality.summary }}</p>
        </section>

        <section class="report-section">
          <h2>航线</h2>
          <div class="report-grid report-grid-wide">
            <span>模式</span>
            <strong>{{ routeModeLabel(report.recommended_route.mode) }}</strong>
            <span>距离</span>
            <strong>{{ report.recommended_route.distance_m }} 米</strong>
            <span>预计时间</span>
            <strong>{{ report.recommended_route.estimated_time_s }} 秒</strong>
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
              <strong>{{ event.time_s }}秒</strong>
              <span>{{ event.title }}</span>
              <small>{{ event.description }}</small>
            </article>
          </div>
        </section>

        <section class="report-section">
          <h2>视觉匹配</h2>
          <div class="report-grid report-grid-wide" v-if="report.vision_summary">
            <span>输入图数量</span>
            <strong>{{ report.vision_summary.image_count }}</strong>
            <span>最高置信候选</span>
            <strong>{{ report.vision_summary.best_tile_id }} · {{ Math.round(report.vision_summary.best_confidence * 100) }}%</strong>
            <span>平均匹配点</span>
            <strong>{{ report.vision_summary.average_matched_points }}</strong>
            <span>几何验证</span>
            <strong>{{ report.vision_summary.geometry_verified ? "通过" : "需复核" }}</strong>
            <span>复核数量</span>
            <strong>{{ report.vision_summary.needs_review_count }}</strong>
          </div>
          <p class="summary-text" v-if="report.vision_summary">{{ report.vision_summary.summary }}</p>
          <div class="candidate-row" v-for="candidate in report.vision.candidates" :key="candidate.tile_id">
            <span>{{ candidate.tile_id }}</span>
            <strong>{{ Math.round(candidate.confidence * 100) }}%</strong>
            <small>{{ candidate.matched_points }} 个匹配点</small>
            <em>{{ candidate.reason }}</em>
          </div>
        </section>
      </template>
    </section>
  </main>
</template>

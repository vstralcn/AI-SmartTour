<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, LineChart, PieChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
} from 'echarts/components'
import VChart from 'vue-echarts'
import { getDashboardData, type DashboardData } from '../../services/api'

use([
  CanvasRenderer,
  BarChart,
  LineChart,
  PieChart,
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
])

const dashboardData = ref<DashboardData | null>(null)
const loadError = ref('')
const responseChartOption = ref({})
const visitsChartOption = ref({})
const spotChartOption = ref({})
const routePreferenceOption = ref({})

function buildCharts(data: DashboardData) {
  responseChartOption.value = {
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: data.response_time_trend.map((d) => d.date) },
    yAxis: { type: 'value', name: '毫秒' },
    series: [
      {
        data: data.response_time_trend.map((d) => d.value),
        type: 'line',
        smooth: true,
        areaStyle: { color: 'rgba(79, 70, 229, 0.1)' },
        lineStyle: { color: '#4f46e5' },
        itemStyle: { color: '#4f46e5' },
      },
    ],
  }

  visitsChartOption.value = {
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: data.hourly_visits.map((d) => `${d.hour}:00`),
    },
    yAxis: { type: 'value' },
    series: [
      {
        data: data.hourly_visits.map((d) => d.count),
        type: 'bar',
        itemStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: '#667eea' },
              { offset: 1, color: '#764ba2' },
            ],
          },
          borderRadius: [4, 4, 0, 0],
        },
      },
    ],
  }

  spotChartOption.value = {
    tooltip: { trigger: 'item' },
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        data: data.spot_popularity.map((d) => ({
          name: d.name,
          value: d.visits,
        })),
        emphasis: {
          itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0,0,0,0.3)' },
        },
      },
    ],
  }

  routePreferenceOption.value = {
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'value' },
    yAxis: {
      type: 'category',
      data: data.route_preferences.map((item) => item.name).reverse(),
    },
    series: [
      {
        type: 'bar',
        data: data.route_preferences.map((item) => item.count).reverse(),
        itemStyle: { color: '#0ea5e9', borderRadius: [0, 4, 4, 0] },
      },
    ],
  }
}

onMounted(async () => {
  try {
    dashboardData.value = await getDashboardData()
    buildCharts(dashboardData.value)
  } catch {
    loadError.value = '运营数据加载失败，请检查后端和数据库状态。'
  }
})
</script>

<template>
  <div class="dashboard">
    <div class="page-header">
      <div>
        <h1 class="page-title">数据大屏</h1>
        <p v-if="dashboardData">
          实时业务数据 · 更新于 {{ dashboardData.generated_at }}
        </p>
      </div>
      <el-tag v-if="dashboardData" type="success">真实会话聚合</el-tag>
    </div>
    <el-alert v-if="loadError" :title="loadError" type="error" show-icon />

    <template v-if="dashboardData">
    <div class="stat-cards">
      <div class="stat-card">
        <div class="stat-value">{{ dashboardData.today_visitors.toLocaleString() }}</div>
        <div class="stat-label">今日服务人次</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ dashboardData.weekly_visitors.toLocaleString() }}</div>
        <div class="stat-label">本周服务人次</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ dashboardData.total_sessions.toLocaleString() }}</div>
        <div class="stat-label">累计会话数</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ dashboardData.avg_response_ms }}ms</div>
        <div class="stat-label">平均响应时间</div>
      </div>
      <div class="stat-card warning">
        <div class="stat-value">{{ dashboardData.knowledge_gap_count }}</div>
        <div class="stat-label">知识缺口</div>
      </div>
      <div class="stat-card danger">
        <div class="stat-value">{{ dashboardData.negative_feedback_count }}</div>
        <div class="stat-label">负面情绪咨询</div>
      </div>
    </div>

    <div class="charts-row">
      <div class="chart-card">
        <h3>近 7 日平均响应时间</h3>
        <v-chart :option="responseChartOption" style="height: 280px" />
      </div>
      <div class="chart-card">
        <h3>每小时访问量</h3>
        <v-chart :option="visitsChartOption" style="height: 280px" />
      </div>
    </div>

    <div class="charts-row">
      <div class="chart-card">
        <h3>路线偏好</h3>
        <v-chart :option="routePreferenceOption" style="height: 280px" />
      </div>
      <div class="chart-card">
        <h3>景点热度排行</h3>
        <v-chart :option="spotChartOption" style="height: 280px" />
      </div>
    </div>
    <div class="chart-card hot-question-card">
      <h3>热门问答 Top5</h3>
      <div class="hot-questions" v-if="dashboardData.hot_questions.length">
        <div
          v-for="(q, i) in dashboardData.hot_questions"
          :key="i"
          class="question-item"
        >
          <span class="question-rank" :class="`rank-${i + 1}`">{{ i + 1 }}</span>
          <span class="question-text">{{ q.question }}</span>
          <span class="question-count">{{ q.count }}次</span>
        </div>
      </div>
      <p class="empty-state" v-else>游客端产生真实咨询后将自动统计。</p>
    </div>
    </template>
  </div>
</template>

<style scoped>
.dashboard {
  padding: 24px;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 4px;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.page-header p {
  color: #6b7280;
  font-size: 13px;
}

.stat-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  text-align: center;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: #4f46e5;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: #6b7280;
}

.stat-card.warning .stat-value {
  color: #d97706;
}

.stat-card.danger .stat-value {
  color: #dc2626;
}

.charts-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}

.chart-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.chart-card h3 {
  font-size: 16px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 12px;
}

.hot-questions {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 8px 0;
}

.hot-question-card {
  margin-bottom: 16px;
}

.empty-state {
  padding: 32px;
  color: #9ca3af;
  text-align: center;
}

.question-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 0;
  border-bottom: 1px solid #f3f4f6;
}

.question-rank {
  width: 24px;
  height: 24px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  color: white;
  background: #9ca3af;
  flex-shrink: 0;
}

.rank-1 { background: #ef4444; }
.rank-2 { background: #f97316; }
.rank-3 { background: #eab308; }

.question-text {
  flex: 1;
  font-size: 14px;
  color: #374151;
}

.question-count {
  font-size: 13px;
  color: #6b7280;
  flex-shrink: 0;
}

@media (max-width: 960px) {
  .stat-cards,
  .charts-row {
    grid-template-columns: 1fr;
  }
}
</style>

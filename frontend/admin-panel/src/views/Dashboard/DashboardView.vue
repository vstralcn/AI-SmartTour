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

const demoDashboard: DashboardData = {
  today_visitors: 1283,
  weekly_visitors: 8742,
  total_sessions: 45892,
  avg_satisfaction: 4.6,
  hot_questions: [
    { question: '景区开放时间是什么？', count: 342 },
    { question: '门票价格多少？', count: 278 },
    { question: '推荐游览路线？', count: 256 },
    { question: '附近有什么餐厅？', count: 198 },
    { question: '景区有哪些历史故事？', count: 176 },
  ],
  satisfaction_trend: [
    { date: '周一', score: 4.5 },
    { date: '周二', score: 4.6 },
    { date: '周三', score: 4.4 },
    { date: '周四', score: 4.7 },
    { date: '周五', score: 4.8 },
    { date: '周六', score: 4.6 },
    { date: '周日', score: 4.5 },
  ],
  hourly_visits: Array.from({ length: 24 }, (_, i) => ({
    hour: i,
    count: Math.max(0, Math.floor(80 * Math.sin(((i - 6) / 12) * Math.PI) + Math.random() * 20)),
  })),
  spot_popularity: [
    { name: '古建筑群', visits: 890 },
    { name: '山水园林', visits: 756 },
    { name: '文化体验馆', visits: 634 },
    { name: '观景台', visits: 521 },
    { name: '入口广场', visits: 412 },
  ],
}

const satisfactionChartOption = ref({})
const visitsChartOption = ref({})
const spotChartOption = ref({})

function buildCharts(data: DashboardData) {
  satisfactionChartOption.value = {
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: data.satisfaction_trend.map((d) => d.date) },
    yAxis: { type: 'value', min: 3, max: 5 },
    series: [
      {
        data: data.satisfaction_trend.map((d) => d.score),
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
}

onMounted(async () => {
  try {
    dashboardData.value = await getDashboardData()
  } catch {
    dashboardData.value = demoDashboard
  }
  buildCharts(dashboardData.value!)
})
</script>

<template>
  <div class="dashboard" v-if="dashboardData">
    <h1 class="page-title">数据大屏</h1>

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
        <div class="stat-value">{{ dashboardData.avg_satisfaction }}</div>
        <div class="stat-label">平均满意度</div>
      </div>
    </div>

    <div class="charts-row">
      <div class="chart-card">
        <h3>满意度趋势</h3>
        <v-chart :option="satisfactionChartOption" style="height: 280px" />
      </div>
      <div class="chart-card">
        <h3>每小时访问量</h3>
        <v-chart :option="visitsChartOption" style="height: 280px" />
      </div>
    </div>

    <div class="charts-row">
      <div class="chart-card">
        <h3>景点热度排行</h3>
        <v-chart :option="spotChartOption" style="height: 280px" />
      </div>
      <div class="chart-card">
        <h3>热门问答 Top5</h3>
        <div class="hot-questions">
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
      </div>
    </div>
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
  margin-bottom: 24px;
}

.stat-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
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
</style>

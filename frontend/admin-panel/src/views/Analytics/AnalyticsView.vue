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
import { getSentimentReport, type SentimentReport } from '../../services/api'

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

const report = ref<SentimentReport | null>(null)
const loadError = ref('')

const sentimentPieOption = ref({})
const sentimentTrendOption = ref({})
const concernsOption = ref({})

function buildCharts(data: SentimentReport) {
  sentimentPieOption.value = {
    tooltip: { trigger: 'item', formatter: '{b}: {d}%' },
    series: [
      {
        type: 'pie',
        radius: ['45%', '70%'],
        data: [
          { name: '正面', value: Math.round(data.positive_ratio * 100), itemStyle: { color: '#22c55e' } },
          { name: '中性', value: Math.round(data.neutral_ratio * 100), itemStyle: { color: '#eab308' } },
          { name: '负面', value: Math.round(data.negative_ratio * 100), itemStyle: { color: '#ef4444' } },
        ],
        label: { formatter: '{b}\n{d}%' },
      },
    ],
  }

  sentimentTrendOption.value = {
    tooltip: { trigger: 'axis' },
    legend: { data: ['正面', '中性', '负面'], bottom: 0 },
    xAxis: { type: 'category', data: data.trend.map((d) => d.date) },
    yAxis: { type: 'value', max: 100 },
    series: [
      {
        name: '正面',
        type: 'line',
        stack: 'total',
        areaStyle: { color: 'rgba(34, 197, 94, 0.3)' },
        lineStyle: { color: '#22c55e' },
        itemStyle: { color: '#22c55e' },
        data: data.trend.map((d) => d.positive),
      },
      {
        name: '中性',
        type: 'line',
        stack: 'total',
        areaStyle: { color: 'rgba(234, 179, 8, 0.3)' },
        lineStyle: { color: '#eab308' },
        itemStyle: { color: '#eab308' },
        data: data.trend.map((d) => d.neutral),
      },
      {
        name: '负面',
        type: 'line',
        stack: 'total',
        areaStyle: { color: 'rgba(239, 68, 68, 0.3)' },
        lineStyle: { color: '#ef4444' },
        itemStyle: { color: '#ef4444' },
        data: data.trend.map((d) => d.negative),
      },
    ],
  }

  concernsOption.value = {
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'value' },
    yAxis: {
      type: 'category',
      data: data.top_concerns.map((c) => c.topic).reverse(),
    },
    series: [
      {
        type: 'bar',
        data: data.top_concerns
          .map((c) => ({
            value: c.count,
            itemStyle: {
              color:
                c.sentiment === 'positive'
                  ? '#22c55e'
                  : c.sentiment === 'negative'
                    ? '#ef4444'
                    : '#eab308',
            },
          }))
          .reverse(),
      },
    ],
  }
}

onMounted(async () => {
  try {
    report.value = await getSentimentReport()
    buildCharts(report.value)
  } catch {
    loadError.value = '情绪分析加载失败，请检查后端和数据库状态。'
  }
})
</script>

<template>
  <div class="analytics-view">
    <h1 class="page-title">游客感受度分析</h1>
    <el-alert v-if="loadError" :title="loadError" type="error" show-icon />

    <template v-if="report">
    <div class="overview-cards">
      <div class="overview-card positive">
        <div class="card-value">{{ Math.round(report.positive_ratio * 100) }}%</div>
        <div class="card-label">正面评价</div>
      </div>
      <div class="overview-card neutral">
        <div class="card-value">{{ Math.round(report.neutral_ratio * 100) }}%</div>
        <div class="card-label">中性评价</div>
      </div>
      <div class="overview-card negative">
        <div class="card-value">{{ Math.round(report.negative_ratio * 100) }}%</div>
        <div class="card-label">负面评价</div>
      </div>
    </div>

    <div class="charts-row">
      <div class="chart-card">
        <h3>情感分布</h3>
        <v-chart :option="sentimentPieOption" style="height: 300px" />
      </div>
      <div class="chart-card">
        <h3>情感趋势</h3>
        <v-chart :option="sentimentTrendOption" style="height: 300px" />
      </div>
    </div>

    <div class="charts-row">
      <div class="chart-card">
        <h3>游客关注热点</h3>
        <v-chart :option="concernsOption" style="height: 300px" />
      </div>
      <div class="chart-card">
        <h3>服务优化建议</h3>
        <div class="suggestions">
          <div v-for="(s, i) in report.suggestions" :key="i" class="suggestion-item">
            <span class="suggestion-number">{{ i + 1 }}</span>
            <p>{{ s }}</p>
          </div>
        </div>
      </div>
    </div>
    </template>
  </div>
</template>

<style scoped>
.analytics-view {
  padding: 24px;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 24px;
}

.overview-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.overview-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  text-align: center;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  border-top: 4px solid;
}

.overview-card.positive { border-color: #22c55e; }
.overview-card.neutral { border-color: #eab308; }
.overview-card.negative { border-color: #ef4444; }

.card-value {
  font-size: 36px;
  font-weight: 700;
}

.positive .card-value { color: #22c55e; }
.neutral .card-value { color: #eab308; }
.negative .card-value { color: #ef4444; }

.card-label {
  font-size: 14px;
  color: #6b7280;
  margin-top: 4px;
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

.suggestions {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 8px 0;
}

.suggestion-item {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.suggestion-number {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #eef2ff;
  color: #4f46e5;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  flex-shrink: 0;
  margin-top: 2px;
}

.suggestion-item p {
  font-size: 14px;
  color: #374151;
  line-height: 1.5;
}
</style>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useChatStore } from '../stores/chat'
import { getRecommendedRoute, type ScenicSpot } from '../services/api'

const router = useRouter()
const chatStore = useChatStore()
const duration = ref(3)
const isLoading = ref(false)
const recommendedRoute = ref<ScenicSpot[]>([])
const routeDescription = ref('')

const demoRoute: ScenicSpot[] = [
  {
    id: '1',
    name: '景区入口广场',
    description: '景区标志性建筑，可以了解景区全貌和历史沿革',
    category: '文化景观',
    recommended_duration: 20,
    tags: ['历史', '地标'],
  },
  {
    id: '2',
    name: '古建筑群',
    description: '保存完好的明清古建筑，展现传统建筑艺术之美',
    category: '历史遗迹',
    recommended_duration: 45,
    tags: ['历史文化', '建筑'],
  },
  {
    id: '3',
    name: '山水园林',
    description: '融合江南园林精髓，亭台楼阁错落有致',
    category: '自然风光',
    recommended_duration: 40,
    tags: ['自然', '园林'],
  },
  {
    id: '4',
    name: '文化体验馆',
    description: '沉浸式体验传统文化，可参与手工艺制作',
    category: '互动体验',
    recommended_duration: 35,
    tags: ['体验', '互动'],
  },
  {
    id: '5',
    name: '观景台',
    description: '景区最高点，可俯瞰全景，是最佳摄影点',
    category: '观景',
    recommended_duration: 30,
    tags: ['观景', '摄影'],
  },
]

async function generateRoute() {
  isLoading.value = true
  try {
    const resp = await getRecommendedRoute({
      session_id: chatStore.sessionId,
      duration_hours: duration.value,
      interests: chatStore.userProfile.interests,
    })
    recommendedRoute.value = resp.route
    routeDescription.value = resp.description
  } catch {
    recommendedRoute.value = demoRoute
    routeDescription.value = `根据您对${chatStore.userProfile.interests.join('、') || '综合游览'}的兴趣，为您规划了约${duration.value}小时的游览路线。路线涵盖景区精华景点，兼顾文化体验和自然风光。`
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="route-view">
    <header class="route-header">
      <button class="back-btn" @click="router.back()">&larr;</button>
      <h1>个性化路线推荐</h1>
    </header>

    <div class="route-config">
      <div class="config-item">
        <label>计划游览时长</label>
        <div class="duration-options">
          <button
            v-for="h in [2, 3, 5, 8]"
            :key="h"
            :class="{ active: duration === h }"
            @click="duration = h"
          >
            {{ h }}小时
          </button>
        </div>
      </div>

      <div class="config-item" v-if="chatStore.userProfile.interests.length">
        <label>您的兴趣标签</label>
        <div class="tags">
          <span
            class="tag"
            v-for="i in chatStore.userProfile.interests"
            :key="i"
          >
            {{ i }}
          </span>
        </div>
      </div>

      <button class="generate-btn" @click="generateRoute" :disabled="isLoading">
        {{ isLoading ? '生成中...' : '生成推荐路线' }}
      </button>
    </div>

    <div class="route-result" v-if="recommendedRoute.length">
      <p class="route-desc">{{ routeDescription }}</p>

      <div class="timeline">
        <div
          v-for="(spot, index) in recommendedRoute"
          :key="spot.id"
          class="timeline-item"
        >
          <div class="timeline-marker">
            <span class="marker-number">{{ index + 1 }}</span>
            <div class="marker-line" v-if="index < recommendedRoute.length - 1"></div>
          </div>
          <div class="timeline-content">
            <h3>{{ spot.name }}</h3>
            <p class="spot-desc">{{ spot.description }}</p>
            <div class="spot-meta">
              <span class="spot-category">{{ spot.category }}</span>
              <span class="spot-duration">约{{ spot.recommended_duration }}分钟</span>
            </div>
            <div class="spot-tags">
              <span class="spot-tag" v-for="t in spot.tags" :key="t">{{ t }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.route-view {
  min-height: 100vh;
  background: #f0f2f5;
}

.route-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: white;
  border-bottom: 1px solid #e5e7eb;
}

.route-header h1 {
  font-size: 18px;
  font-weight: 600;
}

.back-btn {
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
  color: #4f46e5;
}

.route-config {
  padding: 20px 16px;
  background: white;
  margin: 12px;
  border-radius: 12px;
}

.config-item {
  margin-bottom: 16px;
}

.config-item label {
  display: block;
  font-size: 14px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 8px;
}

.duration-options {
  display: flex;
  gap: 8px;
}

.duration-options button {
  flex: 1;
  padding: 8px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  background: white;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.duration-options button.active {
  background: #4f46e5;
  color: white;
  border-color: #4f46e5;
}

.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag {
  padding: 4px 12px;
  background: #eef2ff;
  color: #4f46e5;
  border-radius: 16px;
  font-size: 13px;
}

.generate-btn {
  width: 100%;
  padding: 12px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  margin-top: 8px;
}

.generate-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.route-result {
  padding: 0 16px 32px;
}

.route-desc {
  background: white;
  padding: 16px;
  border-radius: 12px;
  font-size: 14px;
  color: #4b5563;
  line-height: 1.6;
  margin-bottom: 16px;
}

.timeline {
  display: flex;
  flex-direction: column;
}

.timeline-item {
  display: flex;
  gap: 16px;
}

.timeline-marker {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex-shrink: 0;
}

.marker-number {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #4f46e5;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 14px;
}

.marker-line {
  width: 2px;
  flex: 1;
  background: #d1d5db;
  margin: 4px 0;
}

.timeline-content {
  flex: 1;
  background: white;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
}

.timeline-content h3 {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 6px;
}

.spot-desc {
  font-size: 14px;
  color: #6b7280;
  line-height: 1.5;
  margin-bottom: 8px;
}

.spot-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  margin-bottom: 8px;
}

.spot-category {
  color: #4f46e5;
  background: #eef2ff;
  padding: 2px 8px;
  border-radius: 4px;
}

.spot-duration {
  color: #6b7280;
}

.spot-tags {
  display: flex;
  gap: 6px;
}

.spot-tag {
  font-size: 11px;
  padding: 2px 8px;
  background: #f3f4f6;
  color: #6b7280;
  border-radius: 4px;
}
</style>

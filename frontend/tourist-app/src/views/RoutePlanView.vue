<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useChatStore } from '../stores/chat'
import { getRecommendedRoute, type ScenicSpot } from '../services/api'

const router = useRouter()
const chatStore = useChatStore()
const duration = ref(chatStore.userProfile.visitDuration)
const isLoading = ref(false)
const recommendedRoute = ref<ScenicSpot[]>([])
const routeDescription = ref('')
const routeError = ref('')

const durationOptions = [
  { value: 2, label: '2 小时', icon: '⏱' },
  { value: 3, label: '3 小时', icon: '⏱' },
  { value: 5, label: '5 小时', icon: '🕐' },
  { value: 8, label: '全天', icon: '☀' },
]

const categoryEmoji: Record<string, string> = {
  历史: '🏛',
  文化: '📜',
  自然: '🌿',
  风景: '⛰',
  宗教: '🛕',
  民俗: '🎭',
  美食: '🍜',
  建筑: '🏯',
}

function categoryIcon(category: string): string {
  for (const key in categoryEmoji) {
    if (category.includes(key)) return categoryEmoji[key]
  }
  return '📍'
}

async function generateRoute() {
  isLoading.value = true
  routeError.value = ''
  try {
    const resp = await getRecommendedRoute({
      session_id: chatStore.sessionId,
      duration_hours: duration.value,
      interests: chatStore.userProfile.interests,
      companions: chatStore.userProfile.companions,
      mobility: chatStore.userProfile.mobility,
    })
    recommendedRoute.value = resp.route
    routeDescription.value = resp.description
  } catch {
    recommendedRoute.value = []
    routeDescription.value = ''
    routeError.value = '路线服务暂时不可用，请检查后端服务后重试。'
  } finally {
    isLoading.value = false
  }
}

function goBack() {
  router.back()
}
</script>

<template>
  <div class="route-view">
    <header class="route-header">
      <button class="icon-btn" @click="goBack" title="返回">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="19" y1="12" x2="5" y2="12" />
          <polyline points="12 19 5 12 12 5" />
        </svg>
      </button>
      <div class="header-title">
        <h1>个性化路线推荐</h1>
        <p>基于您的兴趣与同行人定制</p>
      </div>
    </header>

    <div class="route-body">
      <section class="config-card">
        <div class="config-item">
          <label>计划游览时长</label>
          <div class="duration-grid">
            <button
              v-for="opt in durationOptions"
              :key="opt.value"
              class="duration-card"
              :class="{ active: duration === opt.value }"
              @click="duration = opt.value"
            >
              <span class="duration-icon">{{ opt.icon }}</span>
              <span class="duration-label">{{ opt.label }}</span>
            </button>
          </div>
        </div>

        <div v-if="chatStore.userProfile.interests.length" class="config-item">
          <label>您的兴趣标签</label>
          <div class="tags">
            <span class="tag tag-brand" v-for="i in chatStore.userProfile.interests" :key="i">
              {{ i }}
            </span>
          </div>
        </div>

        <div class="config-item">
          <label>画像约束</label>
          <div class="tags">
            <span v-for="item in chatStore.userProfile.companions" :key="item" class="tag tag-soft">
              同行：{{ item }}
            </span>
            <span class="tag tag-soft">强度：{{ chatStore.userProfile.mobility }}</span>
          </div>
        </div>

        <button class="generate-btn" @click="generateRoute" :disabled="isLoading">
          <span v-if="!isLoading" class="btn-content">
            <span>生成推荐路线</span>
            <span class="arrow">→</span>
          </span>
          <span v-else class="btn-loading">
            <span class="loading-spinner" />
            <span>正在为您规划…</span>
          </span>
        </button>

        <transition name="fade-down">
          <p v-if="routeError" class="route-error">
            <span class="error-icon">⚠</span>
            {{ routeError }}
          </p>
        </transition>
      </section>

      <transition name="fade-up">
        <section v-if="recommendedRoute.length" class="result-section">
          <div class="result-header">
            <h2>推荐路线</h2>
            <span class="result-count">{{ recommendedRoute.length }} 个景点 · 约 {{ recommendedRoute.reduce((s, x) => s + x.recommended_duration, 0) }} 分钟</span>
          </div>

          <p v-if="routeDescription" class="route-desc">{{ routeDescription }}</p>

          <div class="timeline">
            <div
              v-for="(spot, index) in recommendedRoute"
              :key="spot.id"
              class="timeline-item"
            >
              <div class="timeline-marker">
                <span class="marker-number">{{ index + 1 }}</span>
                <div v-if="index < recommendedRoute.length - 1" class="marker-line" />
              </div>
              <div class="timeline-content">
                <div class="spot-head">
                  <span class="spot-emoji">{{ categoryIcon(spot.category) }}</span>
                  <div class="spot-title-block">
                    <h3>{{ spot.name }}</h3>
                    <span class="spot-category">{{ spot.category }}</span>
                  </div>
                  <span class="spot-duration">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <circle cx="12" cy="12" r="10" />
                      <polyline points="12 6 12 12 16 14" />
                    </svg>
                    约 {{ spot.recommended_duration }} 分钟
                  </span>
                </div>
                <p class="spot-desc">{{ spot.description }}</p>
                <div v-if="spot.tags?.length" class="spot-tags">
                  <span class="spot-tag" v-for="t in spot.tags" :key="t">#{{ t }}</span>
                </div>
              </div>
            </div>
          </div>
        </section>
      </transition>
    </div>
  </div>
</template>

<style scoped>
.route-view {
  min-height: 100vh;
  background: var(--color-bg);
  padding-bottom: var(--sp-7);
}

.route-header {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  padding: 14px var(--sp-5);
  background: rgba(255, 255, 255, 0.78);
  backdrop-filter: saturate(180%) blur(20px);
  -webkit-backdrop-filter: saturate(180%) blur(20px);
  border-bottom: 1px solid var(--color-border-2);
  position: sticky;
  top: 0;
  z-index: 10;
}

.icon-btn {
  width: 36px;
  height: 36px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  color: var(--brand-600);
  border-radius: var(--r-md);
  transition: all var(--t-fast) var(--ease-out);
}
.icon-btn:hover {
  background: var(--brand-50);
}

.header-title h1 {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text);
}
.header-title p {
  font-size: 11px;
  color: var(--color-text-3);
  margin-top: 2px;
}

.route-body {
  max-width: 720px;
  margin: 0 auto;
  padding: var(--sp-4);
  display: flex;
  flex-direction: column;
  gap: var(--sp-4);
}

.config-card {
  background: var(--color-surface);
  border-radius: var(--r-2xl);
  padding: var(--sp-5);
  box-shadow: var(--shadow-sm);
  display: flex;
  flex-direction: column;
  gap: var(--sp-5);
}

.config-item label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-2);
  margin-bottom: var(--sp-3);
}

.duration-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--sp-2);
}

.duration-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 12px 6px;
  background: var(--color-surface-2);
  border: 1.5px solid var(--color-border-2);
  border-radius: var(--r-lg);
  color: var(--color-text-2);
  cursor: pointer;
  transition: all var(--t-fast) var(--ease-out);
}
.duration-card:hover {
  border-color: var(--brand-300);
  transform: translateY(-1px);
}
.duration-card.active {
  background: var(--brand-500);
  color: #fff;
  border-color: var(--brand-500);
  box-shadow: var(--shadow-glow-soft);
}
.duration-icon {
  font-size: 18px;
  line-height: 1;
}
.duration-label {
  font-size: 12px;
  font-weight: 500;
}

.tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--sp-2);
}

.tag {
  padding: 4px 12px;
  border-radius: var(--r-pill);
  font-size: 12px;
  font-weight: 500;
}
.tag-brand {
  background: var(--brand-500);
  color: #fff;
}
.tag-soft {
  background: var(--color-surface-2);
  color: var(--color-text-2);
  border: 1px solid var(--color-border-2);
}

.generate-btn {
  width: 100%;
  padding: 14px;
  background: var(--gradient-brand);
  color: #fff;
  border: none;
  border-radius: var(--r-pill);
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: var(--shadow-glow);
  transition: all var(--t-normal) var(--ease-out);
}
.generate-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 12px 32px rgba(99, 102, 241, 0.36);
}
.generate-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.btn-content {
  display: inline-flex;
  align-items: center;
  gap: var(--sp-2);
}
.arrow {
  font-size: 18px;
  line-height: 1;
  transition: transform var(--t-normal) var(--ease-out);
}
.generate-btn:hover .arrow {
  transform: translateX(4px);
}

.btn-loading {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}
.loading-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.route-error {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: var(--sp-3) var(--sp-4);
  background: var(--color-warning-soft);
  color: #92400e;
  border-radius: var(--r-md);
  font-size: 13px;
  border: 1px solid rgba(245, 158, 11, 0.2);
}

.fade-down-enter-active,
.fade-down-leave-active {
  transition: all var(--t-normal) var(--ease-out);
}
.fade-down-enter-from,
.fade-down-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

.result-section {
  background: var(--color-surface);
  border-radius: var(--r-2xl);
  padding: var(--sp-5);
  box-shadow: var(--shadow-sm);
}

.result-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: var(--sp-3);
}
.result-header h2 {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text);
}
.result-count {
  font-size: 12px;
  color: var(--color-text-3);
}

.route-desc {
  background: var(--brand-50);
  border: 1px solid var(--brand-100);
  border-radius: var(--r-lg);
  padding: var(--sp-3) var(--sp-4);
  font-size: 13px;
  color: var(--brand-800);
  line-height: 1.7;
  margin-bottom: var(--sp-5);
}

.fade-up-enter-active,
.fade-up-leave-active {
  transition: all var(--t-slow) var(--ease-out);
}
.fade-up-enter-from,
.fade-up-leave-to {
  opacity: 0;
  transform: translateY(12px);
}

.timeline {
  display: flex;
  flex-direction: column;
}

.timeline-item {
  display: flex;
  gap: var(--sp-4);
}

.timeline-marker {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex-shrink: 0;
  width: 32px;
}

.marker-number {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--gradient-brand);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 13px;
  box-shadow: var(--shadow-glow-soft);
  flex-shrink: 0;
}

.marker-line {
  width: 2px;
  flex: 1;
  background: linear-gradient(180deg, var(--brand-200) 0%, var(--color-border) 100%);
  margin: 4px 0;
  min-height: 16px;
  border-radius: var(--r-pill);
}

.timeline-content {
  flex: 1;
  background: var(--color-surface-2);
  border: 1px solid var(--color-border-2);
  border-radius: var(--r-lg);
  padding: var(--sp-4);
  margin-bottom: var(--sp-3);
  transition: all var(--t-normal) var(--ease-out);
}
.timeline-content:hover {
  border-color: var(--brand-200);
  box-shadow: var(--shadow-sm);
  transform: translateX(2px);
}

.spot-head {
  display: flex;
  align-items: flex-start;
  gap: var(--sp-3);
  margin-bottom: var(--sp-2);
}

.spot-emoji {
  font-size: 26px;
  line-height: 1;
  flex-shrink: 0;
}

.spot-title-block {
  flex: 1;
  min-width: 0;
}
.spot-title-block h3 {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 2px;
}
.spot-category {
  font-size: 11px;
  color: var(--brand-600);
  background: var(--brand-50);
  padding: 2px 8px;
  border-radius: var(--r-pill);
}

.spot-duration {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: var(--color-text-3);
  flex-shrink: 0;
  padding-top: 4px;
}

.spot-desc {
  font-size: 13px;
  color: var(--color-text-2);
  line-height: 1.65;
  margin-bottom: var(--sp-2);
}

.spot-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}
.spot-tag {
  font-size: 11px;
  padding: 2px 8px;
  background: var(--color-surface);
  color: var(--color-text-3);
  border-radius: var(--r-pill);
  border: 1px solid var(--color-border-2);
}

@media (max-width: 520px) {
  .duration-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>

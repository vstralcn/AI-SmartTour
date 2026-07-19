<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useChatStore } from '../stores/chat'
import { createSession } from '../services/api'

const router = useRouter()
const chatStore = useChatStore()
const selectedInterests = ref<string[]>([])
const ageGroup = ref('成人')
const companions = ref<string[]>([])
const mobility = ref('标准')
const visitDuration = ref(3)
const isStarting = ref(false)
const connectionError = ref('')

const interestOptions = [
  { label: '历史文化', value: '历史文化', icon: '🏛️' },
  { label: '自然风光', value: '自然风光', icon: '🌿' },
  { label: '民俗体验', value: '民俗体验', icon: '🎭' },
  { label: '美食探索', value: '美食探索', icon: '🍜' },
  { label: '摄影打卡', value: '摄影打卡', icon: '📷' },
  { label: '亲子游玩', value: '亲子游玩', icon: '👨‍👩‍👧' },
]

const companionOptions = ['独自', '朋友', '儿童', '老人']
const ageOptions = ['儿童', '青年', '成人', '老年']
const mobilityOptions = ['标准', '低强度']
const durationOptions = [
  { value: 2, label: '2 小时' },
  { value: 3, label: '3 小时' },
  { value: 5, label: '5 小时' },
  { value: 8, label: '全天' },
]

const canStart = computed(() => selectedInterests.value.length > 0 && !isStarting.value)

function toggleInterest(value: string) {
  const idx = selectedInterests.value.indexOf(value)
  if (idx >= 0) {
    selectedInterests.value.splice(idx, 1)
  } else {
    selectedInterests.value.push(value)
  }
}

function toggleCompanion(value: string) {
  const index = companions.value.indexOf(value)
  if (index >= 0) {
    companions.value.splice(index, 1)
  } else {
    companions.value.push(value)
  }
}

async function startChat() {
  isStarting.value = true
  connectionError.value = ''
  try {
    const resp = await createSession({
      interests: selectedInterests.value,
      age_group: ageGroup.value,
      companions: companions.value,
      mobility: mobility.value,
      visit_duration: visitDuration.value,
    })
    chatStore.setSessionId(resp.session_id)
    chatStore.userProfile.interests = selectedInterests.value
    chatStore.userProfile.ageGroup = ageGroup.value
    chatStore.userProfile.companions = companions.value
    chatStore.userProfile.mobility = mobility.value
    chatStore.userProfile.visitDuration = visitDuration.value
    chatStore.addMessage({
      id: 'greeting',
      role: 'assistant',
      content: resp.greeting,
      timestamp: Date.now(),
      emotion: 'happy',
    })
    router.push('/chat')
  } catch {
    connectionError.value = '暂时无法连接导览服务，请确认 Docker Compose 已启动后重试。'
  } finally {
    isStarting.value = false
  }
}
</script>

<template>
  <div class="home-view">
    <!-- 顶部 Hero：紫蓝渐变 + 装饰光斑 -->
    <section class="hero">
      <div class="hero-blob hero-blob-1" />
      <div class="hero-blob hero-blob-2" />
      <div class="hero-content">
        <div class="hero-badge">AI · 数字人 · 实时导览</div>
        <h1 class="hero-title">智慧景区 AI 导游</h1>
        <p class="hero-subtitle">
          您的专属 AI 数字人导游，提供个性化的智能导览服务
        </p>
        <div class="hero-stats">
          <div class="stat">
            <span class="stat-num">3D</span>
            <span class="stat-label">实时数字人</span>
          </div>
          <div class="stat-divider" />
          <div class="stat">
            <span class="stat-num">RAG</span>
            <span class="stat-label">景区知识库</span>
          </div>
          <div class="stat-divider" />
          <div class="stat">
            <span class="stat-num">TTS</span>
            <span class="stat-label">语音合成</span>
          </div>
        </div>
      </div>
    </section>

    <!-- 兴趣选择：毛玻璃卡片 -->
    <section class="card-section">
      <div class="section-head">
        <h2>选择您的兴趣</h2>
        <p class="hint">选 1-3 个方向，我们为您定制专属导览</p>
      </div>
      <div class="interest-grid">
        <button
          v-for="opt in interestOptions"
          :key="opt.value"
          class="interest-card"
          :class="{ selected: selectedInterests.includes(opt.value) }"
          @click="toggleInterest(opt.value)"
        >
          <span class="interest-icon">{{ opt.icon }}</span>
          <span class="interest-label">{{ opt.label }}</span>
          <span v-if="selectedInterests.includes(opt.value)" class="check-mark">✓</span>
        </button>
      </div>
    </section>

    <!-- 画像完善：圆角分组 -->
    <section class="card-section">
      <div class="section-head">
        <h2>完善游览画像</h2>
        <p class="hint">用于生成更合适的讲解和路线，不需要实名信息</p>
      </div>

      <div class="field-group">
        <div class="field">
          <label>年龄阶段</label>
          <div class="chip-row">
            <button
              v-for="opt in ageOptions"
              :key="opt"
              class="chip"
              :class="{ selected: ageGroup === opt }"
              @click="ageGroup = opt"
            >
              {{ opt }}
            </button>
          </div>
        </div>

        <div class="field">
          <label>游玩时长</label>
          <div class="chip-row">
            <button
              v-for="opt in durationOptions"
              :key="opt.value"
              class="chip"
              :class="{ selected: visitDuration === opt.value }"
              @click="visitDuration = opt.value"
            >
              {{ opt.label }}
            </button>
          </div>
        </div>

        <div class="field">
          <label>游览强度</label>
          <div class="chip-row">
            <button
              v-for="opt in mobilityOptions"
              :key="opt"
              class="chip"
              :class="{ selected: mobility === opt }"
              @click="mobility = opt"
            >
              {{ opt }}
            </button>
          </div>
        </div>

        <div class="field">
          <label>同行人员</label>
          <div class="chip-row">
            <button
              v-for="item in companionOptions"
              :key="item"
              class="chip"
              :class="{ selected: companions.includes(item) }"
              @click="toggleCompanion(item)"
            >
              {{ item }}
            </button>
          </div>
        </div>
      </div>
    </section>

    <!-- 启动按钮 -->
    <section class="action-section">
      <button class="start-btn" :disabled="!canStart" @click="startChat">
        <span class="btn-shine" />
        <span class="btn-text">
          {{ isStarting ? '正在连接…' : '开始智能导览' }}
        </span>
        <span v-if="!isStarting" class="btn-arrow">→</span>
      </button>
      <p v-if="!selectedInterests.length" class="hint-center">
        请先选择至少一个兴趣方向
      </p>
      <p v-if="connectionError" class="error-text">{{ connectionError }}</p>
    </section>
  </div>
</template>

<style scoped>
.home-view {
  min-height: 100vh;
  padding-bottom: var(--sp-9);
}

/* ============== Hero ============== */
.hero {
  position: relative;
  padding: var(--sp-9) var(--sp-6) calc(var(--sp-9) + 32px);
  background: var(--gradient-brand);
  border-radius: 0 0 var(--r-3xl) var(--r-3xl);
  overflow: hidden;
  text-align: center;
  color: #fff;
  box-shadow: 0 8px 32px rgba(99, 102, 241, 0.18);
}

.hero-blob {
  position: absolute;
  border-radius: 50%;
  filter: blur(60px);
  opacity: 0.5;
  pointer-events: none;
}
.hero-blob-1 {
  width: 280px;
  height: 280px;
  background: #f472b6;
  top: -80px;
  left: -60px;
}
.hero-blob-2 {
  width: 320px;
  height: 320px;
  background: #38bdf8;
  bottom: -100px;
  right: -80px;
}

.hero-content {
  position: relative;
  z-index: 1;
  max-width: 720px;
  margin: 0 auto;
}

.hero-badge {
  display: inline-block;
  padding: 6px 14px;
  background: rgba(255, 255, 255, 0.18);
  border: 1px solid rgba(255, 255, 255, 0.25);
  backdrop-filter: blur(10px);
  border-radius: var(--r-pill);
  font-size: 12px;
  font-weight: 500;
  letter-spacing: 0.5px;
  margin-bottom: var(--sp-5);
}

.hero-title {
  font-size: 38px;
  font-weight: 700;
  letter-spacing: -0.5px;
  margin-bottom: var(--sp-3);
  text-shadow: 0 2px 16px rgba(0, 0, 0, 0.12);
}

.hero-subtitle {
  font-size: 15px;
  opacity: 0.92;
  line-height: 1.6;
  max-width: 480px;
  margin: 0 auto var(--sp-6);
}

.hero-stats {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--sp-5);
  padding: var(--sp-4) var(--sp-5);
  background: rgba(255, 255, 255, 0.14);
  border: 1px solid rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(12px);
  border-radius: var(--r-xl);
  width: fit-content;
  margin: 0 auto;
}
.stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}
.stat-num {
  font-size: 18px;
  font-weight: 700;
}
.stat-label {
  font-size: 11px;
  opacity: 0.85;
}
.stat-divider {
  width: 1px;
  height: 24px;
  background: rgba(255, 255, 255, 0.3);
}

/* ============== 卡片区 ============== */
.card-section {
  max-width: 640px;
  margin: -32px auto 0;
  padding: 0 var(--sp-5);
  position: relative;
  z-index: 2;
}

.card-section + .card-section {
  margin-top: var(--sp-6);
}

.section-head {
  padding: 0 var(--sp-2);
  margin-bottom: var(--sp-4);
}
.section-head h2 {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 4px;
}
.hint {
  font-size: 13px;
  color: var(--color-text-3);
}

/* 兴趣卡 */
.interest-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--sp-3);
}

.interest-card {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--sp-2);
  padding: var(--sp-5) var(--sp-3);
  background: var(--color-surface);
  border: 2px solid var(--color-border-2);
  border-radius: var(--r-xl);
  cursor: pointer;
  transition: all var(--t-normal) var(--ease-out);
  box-shadow: var(--shadow-xs);
}

.interest-card:hover {
  transform: translateY(-2px);
  border-color: var(--brand-200);
  box-shadow: var(--shadow-md);
}

.interest-card.selected {
  border-color: var(--brand-500);
  background: var(--brand-50);
  box-shadow: var(--shadow-glow-soft);
}

.interest-icon {
  font-size: 30px;
  line-height: 1;
  filter: grayscale(0.2);
  transition: transform var(--t-normal) var(--ease-out);
}
.interest-card:hover .interest-icon,
.interest-card.selected .interest-icon {
  transform: scale(1.1);
  filter: none;
}

.interest-label {
  font-size: 13px;
  color: var(--color-text-2);
  font-weight: 500;
}
.interest-card.selected .interest-label {
  color: var(--brand-700);
  font-weight: 600;
}

.check-mark {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 18px;
  height: 18px;
  background: var(--brand-500);
  color: #fff;
  border-radius: 50%;
  font-size: 11px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
}

/* 画像字段 */
.field-group {
  background: var(--color-surface);
  border-radius: var(--r-2xl);
  padding: var(--sp-5) var(--sp-5);
  box-shadow: var(--shadow-sm);
  display: flex;
  flex-direction: column;
  gap: var(--sp-5);
}

.field label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-2);
  margin-bottom: var(--sp-2);
}

.chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: var(--sp-2);
}

.chip {
  padding: 8px 16px;
  background: var(--color-surface-2);
  border: 1.5px solid var(--color-border-2);
  border-radius: var(--r-pill);
  font-size: 13px;
  color: var(--color-text-2);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--t-fast) var(--ease-out);
}
.chip:hover {
  border-color: var(--brand-300);
  color: var(--brand-700);
}
.chip.selected {
  background: var(--brand-500);
  color: #fff;
  border-color: var(--brand-500);
  box-shadow: var(--shadow-glow-soft);
}

/* ============== 启动按钮 ============== */
.action-section {
  max-width: 640px;
  margin: var(--sp-7) auto 0;
  padding: 0 var(--sp-5);
  text-align: center;
}

.start-btn {
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--sp-2);
  width: 100%;
  padding: 18px var(--sp-6);
  background: var(--gradient-brand);
  color: #fff;
  border: none;
  border-radius: var(--r-pill);
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: var(--shadow-glow);
  transition: all var(--t-normal) var(--ease-out);
}
.start-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 12px 32px rgba(99, 102, 241, 0.36);
}
.start-btn:active:not(:disabled) {
  transform: translateY(0);
}
.start-btn:disabled {
  background: var(--color-border);
  color: var(--color-text-4);
  box-shadow: none;
  cursor: not-allowed;
}

.btn-shine {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    100deg,
    transparent 30%,
    rgba(255, 255, 255, 0.3) 50%,
    transparent 70%
  );
  transform: translateX(-100%);
  transition: transform 0.6s;
}
.start-btn:hover .btn-shine {
  transform: translateX(100%);
}

.btn-arrow {
  font-size: 20px;
  line-height: 1;
  transition: transform var(--t-normal) var(--ease-out);
}
.start-btn:hover .btn-arrow {
  transform: translateX(4px);
}

.hint-center {
  margin-top: var(--sp-3);
  color: var(--color-text-3);
  font-size: 12px;
}

.error-text {
  margin-top: var(--sp-3);
  padding: var(--sp-3) var(--sp-4);
  background: var(--color-danger-soft);
  color: var(--color-danger);
  border-radius: var(--r-md);
  font-size: 13px;
  border: 1px solid rgba(239, 68, 68, 0.2);
}

/* ============== 响应式 ============== */
@media (max-width: 520px) {
  .hero-title {
    font-size: 28px;
  }
  .hero-stats {
    gap: var(--sp-3);
    padding: var(--sp-3) var(--sp-4);
  }
  .stat-num {
    font-size: 15px;
  }
  .interest-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>

<script setup lang="ts">
import { ref } from 'vue'
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
    <div class="hero-section">
      <div class="hero-bg"></div>
      <div class="hero-content">
        <h1 class="title">智慧景区 AI导游</h1>
        <p class="subtitle">您的专属AI数字人导游，为您提供个性化的智能导览服务</p>
      </div>
    </div>

    <div class="interest-section">
      <h2>选择您的兴趣</h2>
      <p class="hint">选择您感兴趣的方向，我们将为您定制专属导览</p>
      <div class="interest-grid">
        <div
          v-for="opt in interestOptions"
          :key="opt.value"
          class="interest-card"
          :class="{ selected: selectedInterests.includes(opt.value) }"
          @click="toggleInterest(opt.value)"
        >
          <span class="interest-icon">{{ opt.icon }}</span>
          <span class="interest-label">{{ opt.label }}</span>
        </div>
      </div>
    </div>

    <div class="profile-section">
      <h2>完善游览画像</h2>
      <p class="hint">用于生成更合适的讲解和路线，不需要实名信息</p>
      <div class="profile-grid">
        <label class="profile-field">
          <span>年龄阶段</span>
          <select v-model="ageGroup">
            <option>儿童</option>
            <option>青年</option>
            <option>成人</option>
            <option>老年</option>
          </select>
        </label>
        <label class="profile-field">
          <span>游玩时长</span>
          <select v-model.number="visitDuration">
            <option :value="2">2 小时</option>
            <option :value="3">3 小时</option>
            <option :value="5">5 小时</option>
            <option :value="8">全天</option>
          </select>
        </label>
        <label class="profile-field">
          <span>游览强度</span>
          <select v-model="mobility">
            <option>标准</option>
            <option>低强度</option>
          </select>
        </label>
      </div>
      <div class="companion-field">
        <span>同行人员</span>
        <div class="companion-options">
          <button
            v-for="item in companionOptions"
            :key="item"
            :class="{ selected: companions.includes(item) }"
            @click="toggleCompanion(item)"
          >
            {{ item }}
          </button>
        </div>
      </div>
    </div>

    <div class="action-section">
      <button class="start-btn" @click="startChat" :disabled="isStarting">
        {{ isStarting ? '正在连接...' : '开始智能导览' }}
      </button>
      <p v-if="connectionError" class="connection-error">{{ connectionError }}</p>
    </div>
  </div>
</template>

<style scoped>
.home-view {
  min-height: 100vh;
  background: #f0f2f5;
}

.hero-section {
  position: relative;
  height: 280px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.hero-bg {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.hero-content {
  position: relative;
  text-align: center;
  color: white;
  padding: 0 24px;
}

.title {
  font-size: 36px;
  font-weight: 700;
  margin-bottom: 12px;
}

.subtitle {
  font-size: 16px;
  opacity: 0.9;
}

.connection-error {
  margin-top: 12px;
  color: #dc2626;
  font-size: 14px;
}

.interest-section {
  padding: 32px 24px;
  max-width: 600px;
  margin: -40px auto 0;
  position: relative;
}

.profile-section {
  max-width: 600px;
  margin: 0 auto;
  padding: 0 24px 20px;
}

.profile-section h2 {
  font-size: 20px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 8px;
}

.profile-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.profile-field {
  display: flex;
  flex-direction: column;
  gap: 8px;
  color: #4b5563;
  font-size: 13px;
}

.profile-field select {
  border: 1px solid #d1d5db;
  border-radius: 10px;
  background: white;
  padding: 10px;
  color: #1f2937;
}

.companion-field {
  margin-top: 16px;
  color: #4b5563;
  font-size: 13px;
}

.companion-options {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

.companion-options button {
  flex: 1;
  padding: 9px;
  border: 1px solid #d1d5db;
  border-radius: 10px;
  background: white;
  color: #4b5563;
  cursor: pointer;
}

.companion-options button.selected {
  border-color: #4f46e5;
  background: #eef2ff;
  color: #4f46e5;
}

.interest-section h2 {
  font-size: 20px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 8px;
}

.hint {
  font-size: 14px;
  color: #6b7280;
  margin-bottom: 20px;
}

.interest-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.interest-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 20px 12px;
  background: white;
  border-radius: 12px;
  border: 2px solid transparent;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.interest-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.interest-card.selected {
  border-color: #4f46e5;
  background: #eef2ff;
}

.interest-icon {
  font-size: 32px;
}

.interest-label {
  font-size: 14px;
  color: #374151;
  font-weight: 500;
}

.action-section {
  padding: 16px 24px 40px;
  max-width: 600px;
  margin: 0 auto;
}

.start-btn {
  width: 100%;
  padding: 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 18px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s;
}

.start-btn:hover:not(:disabled) {
  opacity: 0.9;
}

.start-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

@media (max-width: 520px) {
  .profile-grid {
    grid-template-columns: 1fr;
  }
}
</style>

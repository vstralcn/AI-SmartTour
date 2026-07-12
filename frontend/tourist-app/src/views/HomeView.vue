<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useChatStore } from '../stores/chat'
import { createSession } from '../services/api'

const router = useRouter()
const chatStore = useChatStore()
const selectedInterests = ref<string[]>([])
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

function toggleInterest(value: string) {
  const idx = selectedInterests.value.indexOf(value)
  if (idx >= 0) {
    selectedInterests.value.splice(idx, 1)
  } else {
    selectedInterests.value.push(value)
  }
}

async function startChat() {
  isStarting.value = true
  connectionError.value = ''
  try {
    const resp = await createSession({
      interests: selectedInterests.value,
    })
    chatStore.setSessionId(resp.session_id)
    chatStore.userProfile.interests = selectedInterests.value
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
</style>

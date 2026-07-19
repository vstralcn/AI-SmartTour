<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  useChatStore,
  type AgentStep,
  type ChatMessage,
  type KnowledgeSource,
} from '../stores/chat'
import {
  createChatWebSocket,
  getActiveAvatar,
  getBroadcastJob,
  getBroadcastVideoUrl,
  requestBroadcast,
  type AvatarConfig,
  type BroadcastJob,
} from '../services/api'
import { cancelSpeech, speakText } from '../services/speech'
import DigitalHuman from '../components/DigitalHuman/DigitalHuman.vue'
import ChatPanel from '../components/ChatPanel/ChatPanel.vue'
import VoiceInput from '../components/VoiceInput/VoiceInput.vue'

const router = useRouter()
const chatStore = useChatStore()
const isSpeaking = ref(false)
const isThinking = ref(false)
const voiceEnabled = ref(true)
/** 数字人呈现模式：live=3D实时互动，hd=高清播报视频 */
const displayMode = ref<'live' | 'hd'>('live')
const speechPulse = ref(0)
const hdVideoUrl = ref('')
const hdVideoMuted = ref(true)
const hdGenerating = ref(false)
const hdError = ref('')
/** 高清播报请求序号，用于丢弃过期结果 */
let hdSeq = 0
const ws = ref<WebSocket | null>(null)
const activeAvatar = ref<AvatarConfig>({
  id: 'xiaozhi',
  name: '小智',
  appearance: {
    image_url: '/avatars/xiaozhi.png',
    style: '现代国风',
  },
  voice_config: {
    voice_id: 'female-1',
    speed: 1,
    pitch: 1.05,
  },
  personality: '热情开朗，善于讲故事',
  gender: '女',
  clothing: '现代导游服',
  speaking_style: '亲切活泼',
  is_active: true,
})

onMounted(async () => {
  if (!chatStore.sessionId) {
    router.push('/')
    return
  }
  try {
    activeAvatar.value = await getActiveAvatar()
  } catch {
    console.warn('使用本地默认数字人配置')
  }
  connectWebSocket()
  const greeting = chatStore.messages.find(
    (message) => message.role === 'assistant'
  )
  if (greeting) {
    deliverResponse(greeting.content)
  }
})

onUnmounted(() => {
  hdSeq++
  ws.value?.close()
  cancelSpeech()
})

function connectWebSocket() {
  try {
    ws.value = createChatWebSocket(chatStore.sessionId)

    ws.value.onmessage = (event) => {
      const data = JSON.parse(event.data)
      handleServerMessage(data)
    }

    ws.value.onerror = () => {
      console.warn('WebSocket连接失败')
    }

    ws.value.onclose = () => {
      console.log('WebSocket已断开')
    }
  } catch {
    console.warn('WebSocket不可用')
  }
}

function getAssistantDraft(): ChatMessage {
  const lastMsg = chatStore.messages[chatStore.messages.length - 1]
  if (lastMsg?.role === 'assistant') {
    return lastMsg
  }

  const draft: ChatMessage = {
    id: `bot-${Date.now()}`,
    role: 'assistant',
    content: '',
    timestamp: Date.now(),
    emotion: chatStore.currentEmotion,
    agentSteps: [],
    sources: [],
  }
  chatStore.addMessage(draft)
  return draft
}

function handleServerMessage(data: {
  type: string
  content: string | AgentStep | KnowledgeSource[]
  done?: boolean
}) {
  if (data.type === 'text_chunk') {
    if (data.done) {
      chatStore.setLoading(false)
      isThinking.value = false
      const message = chatStore.messages[chatStore.messages.length - 1]
      if (message?.role === 'assistant') {
        deliverResponse(message.content)
      }
      return
    }
    getAssistantDraft().content += data.content as string
  } else if (data.type === 'emotion') {
    chatStore.setEmotion(data.content as string)
  } else if (data.type === 'agent_step') {
    getAssistantDraft().agentSteps?.push(data.content as AgentStep)
  } else if (data.type === 'sources') {
    getAssistantDraft().sources = data.content as KnowledgeSource[]
  } else if (data.type === 'error') {
    getAssistantDraft().content = `服务暂时不可用：${data.content as string}`
    chatStore.setLoading(false)
    isThinking.value = false
    isSpeaking.value = false
  }
}

function speakResponse(text: string) {
  if (!voiceEnabled.value) {
    isSpeaking.value = false
    return
  }
  const started = speakText(
    text,
    activeAvatar.value.voice_config,
    {
      onStart: () => {
        isSpeaking.value = true
      },
      onEnd: () => {
        isSpeaking.value = false
      },
      onBoundary: () => {
        speechPulse.value++
      },
    }
  )
  if (!started) {
    isSpeaking.value = false
  }
}

/** 回复投递：按当前呈现模式选择实时语音或高清播报 */
function deliverResponse(text: string) {
  if (!voiceEnabled.value) {
    isSpeaking.value = false
    return
  }
  if (displayMode.value === 'hd') {
    void startHdBroadcast(text)
    return
  }
  speakResponse(text)
}

/** 高清播报：请求后端生成数字人视频，成功后切换视频播放 */
async function startHdBroadcast(text: string) {
  const seq = ++hdSeq
  hdGenerating.value = true
  hdError.value = ''
  hdVideoUrl.value = ''
  try {
    const job = await requestBroadcast(
      text,
      chatStore.currentEmotion,
      activeAvatar.value.appearance.image_url
    )
    const result = await pollBroadcast(job.job_id, seq)
    if (seq !== hdSeq) return
    if (result.status !== 'done') {
      throw new Error(result.message || '高清播报生成失败')
    }
    hdVideoMuted.value = !result.has_audio
    hdVideoUrl.value = getBroadcastVideoUrl(job.job_id)
    if (result.has_audio) {
      // 视频自带配音，由视频播放驱动说话状态
      isSpeaking.value = true
    } else {
      // 模拟视频无音轨，浏览器 TTS 同步发声
      speakResponse(text)
    }
  } catch (err) {
    if (seq !== hdSeq) return
    console.warn('高清播报不可用，降级为实时播报:', err)
    hdError.value = '高清播报暂不可用，已切换实时播报'
    speakResponse(text)
  } finally {
    if (seq === hdSeq) {
      hdGenerating.value = false
    }
  }
}

async function pollBroadcast(jobId: string, seq: number): Promise<BroadcastJob> {
  const deadline = Date.now() + 120_000
  while (Date.now() < deadline) {
    await new Promise((resolve) => setTimeout(resolve, 2000))
    if (seq !== hdSeq) {
      return { job_id: jobId, status: 'failed', message: '已取消' }
    }
    const job = await getBroadcastJob(jobId)
    if (job.status === 'done' || job.status === 'failed') {
      return job
    }
  }
  return { job_id: jobId, status: 'failed', message: '生成超时' }
}

function setDisplayMode(mode: 'live' | 'hd') {
  if (displayMode.value === mode) return
  displayMode.value = mode
  hdSeq++
  hdVideoUrl.value = ''
  hdError.value = ''
  hdGenerating.value = false
  cancelSpeech()
  isSpeaking.value = false
}

function onVideoEnded() {
  hdVideoUrl.value = ''
  isSpeaking.value = false
}

function toggleVoice() {
  voiceEnabled.value = !voiceEnabled.value
  if (!voiceEnabled.value) {
    cancelSpeech()
    isSpeaking.value = false
  }
}

function handleSendMessage(text: string) {
  cancelSpeech()
  isSpeaking.value = false
  chatStore.addMessage({
    id: `user-${Date.now()}`,
    role: 'user',
    content: text,
    timestamp: Date.now(),
  })

  chatStore.setLoading(true)
  isThinking.value = true

  if (ws.value && ws.value.readyState === WebSocket.OPEN) {
    ws.value.send(
      JSON.stringify({
        type: 'text',
        content: text,
        session_id: chatStore.sessionId,
      })
    )
  } else {
    appendConnectionError()
  }
}

function appendConnectionError() {
  chatStore.addMessage({
    id: `bot-${Date.now()}`,
    role: 'assistant',
    content: '导览服务连接已断开，请刷新页面或检查后端服务。',
    timestamp: Date.now(),
    emotion: 'caring',
  })
  chatStore.setEmotion('caring')
  chatStore.setLoading(false)
  isThinking.value = false
  isSpeaking.value = false
}

function goBack() {
  cancelSpeech()
  chatStore.clearMessages()
  router.push('/')
}
</script>

<template>
  <div class="chat-view">
    <header class="chat-header">
      <button class="back-btn" @click="goBack">&larr;</button>
      <h1>AI智能导游</h1>
      <div class="header-actions">
        <button
          class="mode-btn"
          :class="{ active: displayMode === 'live' }"
          @click="setDisplayMode('live')"
          title="3D 实时数字人互动"
        >
          实时
        </button>
        <button
          class="mode-btn"
          :class="{ active: displayMode === 'hd' }"
          @click="setDisplayMode('hd')"
          title="高清播报视频"
        >
          高清
        </button>
        <button class="voice-toggle" @click="toggleVoice">
          {{ voiceEnabled ? '语音开' : '语音关' }}
        </button>
        <button class="route-btn" @click="router.push('/route-plan')">
          路线
        </button>
      </div>
    </header>

    <div class="chat-body">
      <div class="digital-human-section">
        <div class="display-toolbar" v-if="hdError">
          <span class="hd-error">{{ hdError }}</span>
        </div>
        <DigitalHuman
          :emotion="chatStore.currentEmotion"
          :is-speaking="isSpeaking"
          :is-thinking="isThinking"
          :avatar-url="activeAvatar.appearance.image_url"
          :name="activeAvatar.name"
          :style="`${activeAvatar.clothing} · ${activeAvatar.speaking_style}`"
          :introduction="activeAvatar.personality"
          :video-url="hdVideoUrl"
          :video-muted="hdVideoMuted"
          :model-url="'/models/guide.vrm'"
          :speech-pulse="speechPulse"
          @video-ended="onVideoEnded"
        />
      </div>

      <div class="chat-section">
        <ChatPanel @send="handleSendMessage" />
        <div class="voice-section">
          <VoiceInput @transcript="handleSendMessage" />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.chat-view {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f0f2f5;
}

.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: white;
  border-bottom: 1px solid #e5e7eb;
}

.chat-header h1 {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
}

.back-btn {
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
  padding: 4px 8px;
  color: #4f46e5;
}

.route-btn {
  background: #eef2ff;
  color: #4f46e5;
  border: none;
  border-radius: 8px;
  padding: 6px 12px;
  font-size: 13px;
  cursor: pointer;
  font-weight: 500;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.voice-toggle {
  border: none;
  border-radius: 8px;
  background: #ecfdf5;
  color: #047857;
  padding: 6px 10px;
  font-size: 12px;
  cursor: pointer;
}

.mode-btn {
  border: 1px solid #d1d5db;
  border-radius: 8px;
  background: white;
  color: #6b7280;
  padding: 5px 10px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.mode-btn.active {
  background: #4f46e5;
  color: white;
  border-color: #4f46e5;
}

.hd-error {
  display: inline-block;
  margin-bottom: 6px;
  padding: 4px 12px;
  border-radius: 6px;
  background: rgba(239, 68, 68, 0.12);
  color: #ef4444;
  font-size: 11px;
}

.chat-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.digital-human-section {
  height: 380px;
  padding: 12px;
  flex-shrink: 0;
}

.chat-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.voice-section {
  display: flex;
  justify-content: center;
  padding: 8px;
  background: white;
  border-top: 1px solid #e5e7eb;
}

@media (min-width: 768px) {
  .chat-body {
    flex-direction: row;
  }

  .digital-human-section {
    width: 45%;
    height: auto;
  }

  .chat-section {
    width: 55%;
  }
}
</style>

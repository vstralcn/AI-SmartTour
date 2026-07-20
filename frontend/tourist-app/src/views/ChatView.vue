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
import { cancelSpeech, speak } from '../services/speech'
import DigitalHuman from '../components/DigitalHuman/DigitalHuman.vue'
import ChatPanel from '../components/ChatPanel/ChatPanel.vue'
import VoiceInput from '../components/VoiceInput/VoiceInput.vue'

const router = useRouter()
const chatStore = useChatStore()
const isSpeaking = ref(false)
const isThinking = ref(false)
const voiceEnabled = ref(true)
/** 数字人呈现模式：live=3D实时互动，hd=高清播报视频，xunfei=讯飞虚拟人 */
const displayMode = ref<'live' | 'hd' | 'xunfei'>('xunfei')
const speechPulse = ref(0)
/** 讯飞待播报文本与驱动序号 */
const xunfeiText = ref('')
const xunfeiSeq = ref(0)
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
  void speak(
    text,
    activeAvatar.value.voice_config,
    chatStore.currentEmotion,
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
  ).then((started) => {
    if (!started) {
      isSpeaking.value = false
    }
  })
}

/** 回复投递：按当前呈现模式选择实时语音、高清播报或讯飞驱动 */
function deliverResponse(text: string) {
  if (!voiceEnabled.value) {
    isSpeaking.value = false
    return
  }
  if (displayMode.value === 'hd') {
    void startHdBroadcast(text)
    return
  }
  if (displayMode.value === 'xunfei') {
    driveXunfei(text)
    return
  }
  speakResponse(text)
}

/** 讯飞文本驱动：由讯飞形象自行发声，不走浏览器 TTS */
function driveXunfei(text: string) {
  cancelSpeech()
  xunfeiText.value = text
  xunfeiSeq.value++
}

function lastAssistantText(): string {
  for (let i = chatStore.messages.length - 1; i >= 0; i--) {
    if (chatStore.messages[i].role === 'assistant') {
      return chatStore.messages[i].content
    }
  }
  return ''
}

/** 讯飞不可用（未配置/启动失败）：回退实时模式并用浏览器 TTS 补播 */
function onXunfeiError(reason: string) {
  console.warn('讯飞数字人不可用，已切换实时模式:', reason)
  hdError.value = '讯飞数字人暂不可用，已切换实时模式'
  displayMode.value = 'live'
  const text = lastAssistantText()
  if (text) speakResponse(text)
}

/** 讯飞播报状态同步到 UI */
function onXunfeiSpeaking(value: boolean) {
  isSpeaking.value = value
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

function setDisplayMode(mode: 'live' | 'hd' | 'xunfei') {
  if (displayMode.value === mode) return
  displayMode.value = mode
  hdSeq++
  hdVideoUrl.value = ''
  hdError.value = ''
  hdGenerating.value = false
  cancelSpeech()
  isSpeaking.value = false
  // 进入讯飞模式时，把最近一条回复交给讯飞形象播报（未就绪先缓存）
  if (mode === 'xunfei') {
    const text = lastAssistantText()
    if (text) driveXunfei(text)
  }
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
    <!-- 顶部栏：玻璃感 -->
    <header class="chat-header">
      <button class="icon-btn back-btn" @click="goBack" title="返回">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="19" y1="12" x2="5" y2="12" />
          <polyline points="12 19 5 12 12 5" />
        </svg>
      </button>

      <div class="title-block">
        <h1>AI 智能导游</h1>
        <div class="status-line">
          <span class="conn-dot" :class="{ on: ws?.readyState === 1 }" />
          <span class="status-text">
            {{ ws?.readyState === 1 ? '已连接' : '连接中…' }}
          </span>
        </div>
      </div>

      <div class="header-actions">
        <!-- 呈现模式切换 -->
        <div class="seg-group" role="tablist">
          <button
            v-for="m in [
              { key: 'live', label: '实时' },
              { key: 'hd', label: '高清' },
              { key: 'xunfei', label: '讯飞' },
            ]"
            :key="m.key"
            class="seg-btn"
            :class="{ active: displayMode === m.key }"
            @click="setDisplayMode(m.key as 'live' | 'hd' | 'xunfei')"
          >
            {{ m.label }}
          </button>
        </div>

        <button
          class="icon-btn voice-toggle"
          :class="{ off: !voiceEnabled }"
          @click="toggleVoice"
          :title="voiceEnabled ? '关闭语音' : '开启语音'"
        >
          <svg v-if="voiceEnabled" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
            <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07" />
          </svg>
          <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
            <line x1="23" y1="9" x2="17" y2="15" />
            <line x1="17" y1="9" x2="23" y2="15" />
          </svg>
        </button>

        <button class="icon-btn route-btn" @click="router.push('/route-plan')" title="路线规划">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polygon points="3 11 22 2 13 21 11 13 3 11" />
          </svg>
        </button>
      </div>
    </header>

    <div class="chat-body">
      <!-- 数字人区：毛玻璃卡 -->
      <aside class="digital-section">
        <transition name="slide-down">
          <div v-if="hdError" class="hd-banner">
            <span class="banner-dot" />
            <span class="banner-text">{{ hdError }}</span>
          </div>
        </transition>
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
          :enable-xunfei="displayMode === 'xunfei'"
          :xunfei-text="xunfeiText"
          :xunfei-seq="xunfeiSeq"
          @video-ended="onVideoEnded"
          @xunfei-error="onXunfeiError"
          @xunfei-speaking="onXunfeiSpeaking"
        />
      </aside>

      <!-- 聊天区 -->
      <section class="chat-section">
        <ChatPanel @send="handleSendMessage" />
        <div class="voice-section">
          <VoiceInput @transcript="handleSendMessage" />
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.chat-view {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: var(--color-bg);
  overflow: hidden;
}

/* ============== 顶栏 ============== */
.chat-header {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  padding: 12px var(--sp-5);
  background: rgba(255, 255, 255, 0.78);
  backdrop-filter: saturate(180%) blur(20px);
  -webkit-backdrop-filter: saturate(180%) blur(20px);
  border-bottom: 1px solid var(--color-border-2);
  flex-shrink: 0;
  z-index: 10;
}

.title-block {
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin-right: auto;
}

.chat-header h1 {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text);
  letter-spacing: -0.2px;
}

.status-line {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 11px;
  color: var(--color-text-3);
}

.conn-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-text-4);
  transition: all var(--t-normal) var(--ease-out);
}
.conn-dot.on {
  background: var(--color-success);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--color-success) 20%, transparent);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
}

/* 圆角图标按钮 */
.icon-btn {
  width: 36px;
  height: 36px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--color-surface-2);
  color: var(--color-text-2);
  border-radius: var(--r-md);
  transition: all var(--t-fast) var(--ease-out);
}
.icon-btn:hover {
  background: var(--brand-50);
  color: var(--brand-600);
  transform: translateY(-1px);
}

.back-btn {
  background: transparent;
  color: var(--brand-600);
}
.back-btn:hover {
  background: var(--brand-50);
}

.route-btn {
  background: var(--brand-50);
  color: var(--brand-600);
}
.route-btn:hover {
  background: var(--brand-100);
}

.voice-toggle.off {
  background: var(--color-danger-soft);
  color: var(--color-danger);
}
.voice-toggle.off:hover {
  background: var(--color-danger-soft);
  color: var(--color-danger);
}

/* 分段控件（模式切换） */
.seg-group {
  display: inline-flex;
  padding: 3px;
  background: var(--color-surface-2);
  border-radius: var(--r-pill);
  gap: 2px;
}

.seg-btn {
  padding: 5px 14px;
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-3);
  border-radius: var(--r-pill);
  transition: all var(--t-fast) var(--ease-out);
}
.seg-btn:hover {
  color: var(--color-text);
}
.seg-btn.active {
  background: var(--color-surface);
  color: var(--brand-600);
  font-weight: 600;
  box-shadow: var(--shadow-xs);
}

/* ============== 主体 ============== */
.chat-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
}

.digital-section {
  position: relative;
  height: 360px;
  padding: var(--sp-4);
  flex-shrink: 0;
}

.hd-banner {
  position: absolute;
  top: 12px;
  left: 50%;
  transform: translateX(-50%);
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 12px;
  background: var(--color-warning-soft);
  color: #92400e;
  border-radius: var(--r-pill);
  font-size: 11px;
  z-index: 5;
  box-shadow: var(--shadow-sm);
}
.banner-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-warning);
}

.slide-down-enter-active,
.slide-down-leave-active {
  transition: all var(--t-normal) var(--ease-out);
}
.slide-down-enter-from,
.slide-down-leave-to {
  opacity: 0;
  transform: translate(-50%, -8px);
}

.chat-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--color-surface);
  border-radius: var(--r-2xl) var(--r-2xl) 0 0;
  box-shadow: 0 -4px 20px rgba(15, 23, 42, 0.04);
  min-height: 0;
}

.voice-section {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 10px var(--sp-4);
  background: var(--color-surface);
  border-top: 1px solid var(--color-border-2);
}

/* ============== 响应式（桌面） ============== */
@media (min-width: 768px) {
  .chat-body {
    flex-direction: row;
    padding: var(--sp-4);
    gap: var(--sp-4);
  }
  .digital-section {
    width: 45%;
    height: auto;
    padding: 0;
  }
  .chat-section {
    width: 55%;
    border-radius: var(--r-2xl);
  }
}
</style>

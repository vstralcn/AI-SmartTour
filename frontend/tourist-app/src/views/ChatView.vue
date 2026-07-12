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
  type AvatarConfig,
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
    speakResponse(greeting.content)
  }
})

onUnmounted(() => {
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
        speakResponse(message.content)
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
    }
  )
  if (!started) {
    isSpeaking.value = false
  }
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
        <button class="voice-toggle" @click="toggleVoice">
          {{ voiceEnabled ? '语音播报开' : '语音播报关' }}
        </button>
        <button class="route-btn" @click="router.push('/route-plan')">
          路线推荐
        </button>
      </div>
    </header>

    <div class="chat-body">
      <div class="digital-human-section">
        <DigitalHuman
          :emotion="chatStore.currentEmotion"
          :is-speaking="isSpeaking"
          :is-thinking="isThinking"
          :avatar-url="activeAvatar.appearance.image_url"
          :name="activeAvatar.name"
          :style="`${activeAvatar.clothing} · ${activeAvatar.speaking_style}`"
          :introduction="activeAvatar.personality"
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

.chat-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.digital-human-section {
  height: 300px;
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

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  useChatStore,
  type AgentStep,
  type ChatMessage,
  type KnowledgeSource,
} from '../stores/chat'
import { createChatWebSocket } from '../services/api'
import DigitalHuman from '../components/DigitalHuman/DigitalHuman.vue'
import ChatPanel from '../components/ChatPanel/ChatPanel.vue'
import VoiceInput from '../components/VoiceInput/VoiceInput.vue'

const router = useRouter()
const chatStore = useChatStore()
const isSpeaking = ref(false)
const ws = ref<WebSocket | null>(null)

onMounted(() => {
  if (!chatStore.sessionId) {
    router.push('/')
    return
  }
  connectWebSocket()
})

onUnmounted(() => {
  ws.value?.close()
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
      isSpeaking.value = false
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
    isSpeaking.value = false
  }
}

function handleSendMessage(text: string) {
  chatStore.addMessage({
    id: `user-${Date.now()}`,
    role: 'user',
    content: text,
    timestamp: Date.now(),
  })

  chatStore.setLoading(true)
  isSpeaking.value = true

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
  isSpeaking.value = false
}

function handleAudioReady(audio: Blob) {
  chatStore.addMessage({
    id: `user-${Date.now()}`,
    role: 'user',
    content: '[语音消息]',
    timestamp: Date.now(),
  })

  chatStore.setLoading(true)
  isSpeaking.value = true

  if (ws.value && ws.value.readyState === WebSocket.OPEN) {
    const reader = new FileReader()
    reader.onload = () => {
      ws.value?.send(
        JSON.stringify({
          type: 'audio',
          content: reader.result,
          session_id: chatStore.sessionId,
        })
      )
    }
    reader.readAsDataURL(audio)
  } else {
    appendConnectionError()
  }
}

function goBack() {
  chatStore.clearMessages()
  router.push('/')
}
</script>

<template>
  <div class="chat-view">
    <header class="chat-header">
      <button class="back-btn" @click="goBack">&larr;</button>
      <h1>AI智能导游</h1>
      <button class="route-btn" @click="router.push('/route-plan')">
        路线推荐
      </button>
    </header>

    <div class="chat-body">
      <div class="digital-human-section">
        <DigitalHuman
          :emotion="chatStore.currentEmotion"
          :is-speaking="isSpeaking"
        />
      </div>

      <div class="chat-section">
        <ChatPanel @send="handleSendMessage" />
        <div class="voice-section">
          <VoiceInput @audio-ready="handleAudioReady" />
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

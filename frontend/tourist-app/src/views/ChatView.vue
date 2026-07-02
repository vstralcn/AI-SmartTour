<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useChatStore } from '../stores/chat'
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
      console.warn('WebSocket连接失败，使用模拟模式')
    }

    ws.value.onclose = () => {
      console.log('WebSocket已断开')
    }
  } catch {
    console.warn('WebSocket不可用，使用模拟模式')
  }
}

function handleServerMessage(data: {
  type: string
  content: string
  emotion?: string
  done?: boolean
}) {
  if (data.type === 'text_chunk') {
    const lastMsg = chatStore.messages[chatStore.messages.length - 1]
    if (lastMsg && lastMsg.role === 'assistant' && !data.done) {
      lastMsg.content += data.content
    } else if (data.done) {
      chatStore.setLoading(false)
      isSpeaking.value = false
    }
  } else if (data.type === 'emotion') {
    chatStore.setEmotion(data.content)
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
    simulateResponse(text)
  }
}

function simulateResponse(userText: string) {
  const responses: Record<string, string> = {
    default:
      '这是一个很好的问题！让我为您详细介绍一下。这个景点有着悠久的历史，始建于明代，距今已有600多年的历史。这里不仅有精美的建筑，还蕴含着丰富的文化内涵。',
    历史: '这里有着深厚的历史底蕴。据史料记载，早在唐代就已经是著名的游览胜地。历代文人墨客在此留下了大量诗词佳作，是了解中国传统文化的绝佳去处。',
    美食: '说到美食，这里可是美食天堂！推荐您一定要尝尝本地特色小吃，还有传统手工制作的糕点，每一口都是匠心之作。景区内的餐厅"云水间"是最受游客欢迎的用餐地点。',
    路线: '根据您的兴趣，我为您推荐以下游览路线：先参观入口处的历史展览馆（约30分钟），然后沿着古道前行至主景区（约1小时），最后到达观景台欣赏全景。全程约3小时。',
  }

  let responseText = responses.default
  for (const [key, val] of Object.entries(responses)) {
    if (userText.includes(key)) {
      responseText = val
      break
    }
  }

  chatStore.addMessage({
    id: `bot-${Date.now()}`,
    role: 'assistant',
    content: '',
    timestamp: Date.now(),
    emotion: 'explaining',
  })

  chatStore.setEmotion('explaining')

  let idx = 0
  const interval = setInterval(() => {
    const lastMsg = chatStore.messages[chatStore.messages.length - 1]
    if (lastMsg && idx < responseText.length) {
      lastMsg.content += responseText[idx]
      idx++
    } else {
      clearInterval(interval)
      chatStore.setLoading(false)
      isSpeaking.value = false
      chatStore.setEmotion('neutral')
    }
  }, 50)
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
    simulateResponse('语音提问')
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

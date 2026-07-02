<script setup lang="ts">
import { ref, nextTick, watch } from 'vue'
import { useChatStore, type ChatMessage } from '../../stores/chat'

const chatStore = useChatStore()
const inputText = ref('')
const chatContainer = ref<HTMLElement>()

const emit = defineEmits<{
  send: [message: string]
}>()

function handleSend() {
  const text = inputText.value.trim()
  if (!text || chatStore.isLoading) return
  emit('send', text)
  inputText.value = ''
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}

function formatTime(ts: number): string {
  const d = new Date(ts)
  return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

watch(
  () => chatStore.messages.length,
  async () => {
    await nextTick()
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }
  }
)
</script>

<template>
  <div class="chat-panel">
    <div class="chat-messages" ref="chatContainer">
      <div
        v-for="msg in chatStore.messages"
        :key="msg.id"
        class="message"
        :class="msg.role"
      >
        <div class="message-avatar">
          <span v-if="msg.role === 'user'">🧑</span>
          <span v-else>🤖</span>
        </div>
        <div class="message-body">
          <div class="message-content">{{ msg.content }}</div>
          <div class="message-meta">
            <span class="message-time">{{ formatTime(msg.timestamp) }}</span>
            <span v-if="msg.emotion" class="message-emotion">{{ msg.emotion }}</span>
          </div>
        </div>
      </div>
      <div v-if="chatStore.isLoading" class="message assistant">
        <div class="message-avatar"><span>🤖</span></div>
        <div class="message-body">
          <div class="message-content typing">
            <span class="dot"></span>
            <span class="dot"></span>
            <span class="dot"></span>
          </div>
        </div>
      </div>
    </div>

    <div class="chat-input-area">
      <textarea
        v-model="inputText"
        @keydown="handleKeydown"
        placeholder="输入您的问题..."
        rows="1"
        :disabled="chatStore.isLoading"
      ></textarea>
      <button
        class="send-btn"
        @click="handleSend"
        :disabled="!inputText.trim() || chatStore.isLoading"
      >
        发送
      </button>
    </div>
  </div>
</template>

<style scoped>
.chat-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #f8f9fa;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.message {
  display: flex;
  gap: 10px;
  max-width: 85%;
}

.message.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message.assistant {
  align-self: flex-start;
}

.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #e9ecef;
  font-size: 18px;
  flex-shrink: 0;
}

.message-body {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.message-content {
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.6;
  word-break: break-word;
  white-space: pre-wrap;
}

.user .message-content {
  background: #4f46e5;
  color: white;
  border-bottom-right-radius: 4px;
}

.assistant .message-content {
  background: white;
  color: #1f2937;
  border-bottom-left-radius: 4px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.message-meta {
  display: flex;
  gap: 8px;
  font-size: 12px;
  color: #9ca3af;
  padding: 0 4px;
}

.typing {
  display: flex;
  gap: 4px;
  padding: 12px 16px !important;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #9ca3af;
  animation: bounce 1.4s ease-in-out infinite;
}

.dot:nth-child(2) { animation-delay: 0.2s; }
.dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

.chat-input-area {
  display: flex;
  gap: 8px;
  padding: 12px 16px;
  background: white;
  border-top: 1px solid #e5e7eb;
}

.chat-input-area textarea {
  flex: 1;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  padding: 10px 12px;
  font-size: 14px;
  resize: none;
  outline: none;
  font-family: inherit;
}

.chat-input-area textarea:focus {
  border-color: #4f46e5;
  box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.1);
}

.send-btn {
  padding: 10px 20px;
  background: #4f46e5;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: background 0.2s;
}

.send-btn:hover:not(:disabled) {
  background: #4338ca;
}

.send-btn:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}
</style>

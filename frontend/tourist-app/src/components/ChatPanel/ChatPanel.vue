<script setup lang="ts">
import { ref, nextTick, watch, computed } from 'vue'
import { useChatStore, type ChatMessage } from '../../stores/chat'

const chatStore = useChatStore()
const inputText = ref('')
const chatContainer = ref<HTMLElement>()
const isComposing = ref(false)

const emit = defineEmits<{
  send: [message: string]
}>()

const canSend = computed(
  () => inputText.value.trim().length > 0 && !chatStore.isLoading
)

function handleSend() {
  if (!canSend.value || isComposing.value) return
  const text = inputText.value.trim()
  emit('send', text)
  inputText.value = ''
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey && !isComposing.value) {
    e.preventDefault()
    handleSend()
  }
}

function formatTime(ts: number): string {
  const d = new Date(ts)
  return d.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
  })
}

function emotionEmoji(emotion?: string): string {
  const map: Record<string, string> = {
    happy: '😊',
    explaining: '🗣️',
    caring: '🤗',
    excited: '🤩',
    neutral: '💬',
  }
  return emotion ? map[emotion] || '💬' : '💬'
}

function stepEmoji(status: string): string {
  const map: Record<string, string> = {
    success: '✓',
    no_result: '·',
    error: '!',
  }
  return map[status] || '·'
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
      <transition-group name="msg" tag="div" class="msg-stack">
        <div
          v-for="msg in chatStore.messages"
          :key="msg.id"
          class="message"
          :class="msg.role"
        >
          <div class="message-avatar">
            <span v-if="msg.role === 'user'">🧑</span>
            <span v-else>{{ emotionEmoji(msg.emotion) }}</span>
          </div>
          <div class="message-body">
            <div class="message-content">{{ msg.content }}</div>

            <div v-if="msg.agentSteps?.length" class="agent-trace">
              <div class="trace-title">
                <span class="trace-icon">⚙</span>
                <span>Agent 执行轨迹</span>
              </div>
              <div
                v-for="step in msg.agentSteps"
                :key="`${step.tool}-${step.detail}`"
                class="trace-step"
                :class="step.status"
              >
                <span class="trace-status">{{ stepEmoji(step.status) }}</span>
                <span class="trace-detail">{{ step.detail }}</span>
              </div>
            </div>

            <div v-if="msg.sources?.length" class="source-list">
              <div class="source-title">
                <span class="source-icon">📚</span>
                <span>回答依据</span>
              </div>
              <div
                v-for="source in msg.sources"
                :key="`${source.source}-${source.title}`"
                class="source-item"
              >
                <span class="source-name">{{ source.title }}</span>
                <span class="source-score">
                  {{ Math.round(source.score * 100) }}%
                </span>
              </div>
            </div>

            <div class="message-meta">
              <span class="message-time">{{ formatTime(msg.timestamp) }}</span>
              <span v-if="msg.emotion" class="message-emotion">
                {{ emotionEmoji(msg.emotion) }} {{ msg.emotion }}
              </span>
            </div>
          </div>
        </div>

        <!-- 加载占位 -->
        <div v-if="chatStore.isLoading" key="loading" class="message assistant">
          <div class="message-avatar"><span>💬</span></div>
          <div class="message-body">
            <div class="message-content typing">
              <span class="dot"></span>
              <span class="dot"></span>
              <span class="dot"></span>
            </div>
          </div>
        </div>
      </transition-group>
    </div>

    <!-- 输入区 -->
    <div class="chat-input-area">
      <div class="input-wrapper">
        <textarea
          v-model="inputText"
          @keydown="handleKeydown"
          @compositionstart="isComposing = true"
          @compositionend="isComposing = false"
          placeholder="说点什么吧…"
          rows="1"
          :disabled="chatStore.isLoading"
        />
      </div>
      <button
        class="send-btn"
        :class="{ ready: canSend }"
        @click="handleSend"
        :disabled="!canSend"
        title="发送（Enter）"
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="22" y1="2" x2="11" y2="13" />
          <polygon points="22 2 15 22 11 13 2 9 22 2" />
        </svg>
      </button>
    </div>
  </div>
</template>

<style scoped>
.chat-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  background: transparent;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: var(--sp-4);
  min-height: 0;
}

.msg-stack {
  display: flex;
  flex-direction: column;
  gap: var(--sp-4);
}

/* ============== 消息气泡 ============== */
.message {
  display: flex;
  gap: 10px;
  max-width: 88%;
}

.message.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message.assistant {
  align-self: flex-start;
}

.message-avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-surface-2);
  font-size: 17px;
  flex-shrink: 0;
  box-shadow: var(--shadow-xs);
}

.user .message-avatar {
  background: var(--gradient-brand);
  font-size: 16px;
}

.message-body {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.message-content {
  padding: 10px 14px;
  border-radius: var(--r-xl);
  font-size: 14px;
  line-height: 1.65;
  word-break: break-word;
  white-space: pre-wrap;
  position: relative;
}

.user .message-content {
  background: var(--gradient-brand);
  color: #fff;
  border-bottom-right-radius: 6px;
  box-shadow: var(--shadow-glow-soft);
}

.assistant .message-content {
  background: var(--color-surface);
  color: var(--color-text);
  border: 1px solid var(--color-border-2);
  border-bottom-left-radius: 6px;
  box-shadow: var(--shadow-xs);
}

/* ============== Agent 轨迹 ============== */
.agent-trace,
.source-list {
  background: var(--brand-50);
  border: 1px solid var(--brand-100);
  border-radius: var(--r-md);
  padding: 8px 12px;
  font-size: 12px;
  color: var(--brand-800);
}

.trace-title,
.source-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  color: var(--brand-700);
  margin-bottom: 6px;
  font-size: 12px;
}

.trace-icon,
.source-icon {
  font-size: 12px;
}

.trace-step,
.source-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 3px 0;
}

.source-item {
  justify-content: space-between;
}

.trace-status {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 700;
  flex-shrink: 0;
  color: #fff;
  background: var(--color-success);
}
.trace-status.no_result {
  background: var(--color-warning);
}
.trace-status.error {
  background: var(--color-danger);
}

.trace-detail {
  flex: 1;
  color: var(--color-text-2);
}

.source-name {
  color: var(--color-text-2);
}

.source-score {
  font-size: 11px;
  font-weight: 600;
  color: var(--brand-600);
  background: rgba(99, 102, 241, 0.1);
  padding: 2px 8px;
  border-radius: var(--r-pill);
  font-variant-numeric: tabular-nums;
}

.message-meta {
  display: flex;
  gap: 8px;
  font-size: 11px;
  color: var(--color-text-4);
  padding: 0 4px;
}

.message-emotion {
  text-transform: capitalize;
}

/* ============== 打字动画 ============== */
.typing {
  display: flex;
  gap: 5px;
  padding: 14px 18px !important;
}

.dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--brand-400);
  animation: bounce 1.4s ease-in-out infinite;
}
.dot:nth-child(2) { animation-delay: 0.2s; }
.dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes bounce {
  0%, 80%, 100% { transform: translateY(0); opacity: 0.5; }
  40% { transform: translateY(-5px); opacity: 1; }
}

/* ============== 输入区 ============== */
.chat-input-area {
  display: flex;
  gap: var(--sp-2);
  padding: var(--sp-3) var(--sp-4);
  background: var(--color-surface);
  border-top: 1px solid var(--color-border-2);
  align-items: flex-end;
}

.input-wrapper {
  flex: 1;
  background: var(--color-surface-2);
  border: 1.5px solid var(--color-border-2);
  border-radius: var(--r-2xl);
  padding: 4px 6px;
  transition: all var(--t-fast) var(--ease-out);
}
.input-wrapper:focus-within {
  border-color: var(--brand-400);
  background: var(--color-surface);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.chat-input-area textarea {
  width: 100%;
  padding: 8px 10px;
  font-size: 14px;
  resize: none;
  outline: none;
  font-family: inherit;
  background: transparent;
  line-height: 1.5;
  max-height: 120px;
  color: var(--color-text);
}
.chat-input-area textarea::placeholder {
  color: var(--color-text-4);
}

.send-btn {
  width: 42px;
  height: 42px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--color-border-2);
  color: var(--color-text-4);
  border-radius: 50%;
  flex-shrink: 0;
  transition: all var(--t-fast) var(--ease-out);
}
.send-btn.ready {
  background: var(--gradient-brand);
  color: #fff;
  box-shadow: var(--shadow-glow-soft);
}
.send-btn.ready:hover {
  transform: translateY(-1px) scale(1.05);
  box-shadow: var(--shadow-glow);
}

/* ============== 消息进出场 ============== */
.msg-enter-active,
.msg-leave-active {
  transition: all var(--t-normal) var(--ease-out);
}
.msg-enter-from {
  opacity: 0;
  transform: translateY(8px);
}
.msg-leave-to {
  opacity: 0;
}
</style>

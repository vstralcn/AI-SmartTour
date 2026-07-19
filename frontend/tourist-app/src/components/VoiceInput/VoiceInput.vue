<script setup lang="ts">
import { computed, ref } from 'vue'
import { useChatStore } from '../../stores/chat'

const chatStore = useChatStore()
const recognition = ref<SpeechRecognitionLike | null>(null)
const errorMessage = ref('')

const emit = defineEmits<{
  transcript: [text: string]
}>()

interface SpeechRecognitionAlternativeLike {
  transcript: string
}
interface SpeechRecognitionResultLike {
  readonly isFinal: boolean
  readonly [index: number]: SpeechRecognitionAlternativeLike
}
interface SpeechRecognitionResultListLike {
  readonly length: number
  readonly [index: number]: SpeechRecognitionResultLike
}
interface SpeechRecognitionEventLike extends Event {
  readonly results: SpeechRecognitionResultListLike
}
interface SpeechRecognitionErrorEventLike extends Event {
  readonly error: string
}
interface SpeechRecognitionLike {
  lang: string
  continuous: boolean
  interimResults: boolean
  onresult: ((event: SpeechRecognitionEventLike) => void) | null
  onerror: ((event: SpeechRecognitionErrorEventLike) => void) | null
  onend: (() => void) | null
  start: () => void
  stop: () => void
}
interface SpeechRecognitionConstructor {
  new (): SpeechRecognitionLike
}
interface SpeechWindow extends Window {
  SpeechRecognition?: SpeechRecognitionConstructor
  webkitSpeechRecognition?: SpeechRecognitionConstructor
}

const speechWindow = window as SpeechWindow
const Recognition =
  speechWindow.SpeechRecognition || speechWindow.webkitSpeechRecognition
const isSupported = computed(() => Boolean(Recognition))

function startRecording() {
  if (!Recognition) {
    errorMessage.value = '当前浏览器不支持实时语音识别，请使用 Chrome 或文字输入'
    return
  }

  errorMessage.value = ''
  const instance = new Recognition()
  recognition.value = instance
  instance.lang = 'zh-CN'
  instance.continuous = false
  instance.interimResults = false
  instance.onresult = (event) => {
    const result = event.results[event.results.length - 1]
    const transcript = result?.[0]?.transcript.trim()
    if (transcript) {
      emit('transcript', transcript)
    }
  }
  instance.onerror = (event) => {
    errorMessage.value =
      event.error === 'not-allowed'
        ? '请允许浏览器使用麦克风'
        : '没有识别到清晰语音，请重试'
    chatStore.setRecording(false)
  }
  instance.onend = () => {
    chatStore.setRecording(false)
    recognition.value = null
  }
  instance.start()
  chatStore.setRecording(true)
}

function stopRecording() {
  recognition.value?.stop()
  chatStore.setRecording(false)
}

function toggleRecording() {
  if (chatStore.isRecording) {
    stopRecording()
  } else {
    startRecording()
  }
}
</script>

<template>
  <div class="voice-control">
    <button
      v-if="isSupported"
      class="voice-btn"
      :class="{ recording: chatStore.isRecording }"
      @click="toggleRecording"
      :disabled="chatStore.isLoading"
    >
      <span class="ring ring-1" />
      <span class="ring ring-2" />
      <span class="ring ring-3" />

      <span class="mic-core">
        <svg
          v-if="!chatStore.isRecording"
          width="20" height="20" viewBox="0 0 24 24" fill="none"
          stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"
        >
          <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
          <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
          <line x1="12" y1="19" x2="12" y2="23" />
          <line x1="8" y1="23" x2="16" y2="23" />
        </svg>
        <span v-else class="rec-square" />
      </span>
    </button>

    <div class="voice-text">
      <span v-if="!isSupported" class="voice-error">浏览器不支持语音识别</span>
      <span v-else-if="errorMessage" class="voice-error">{{ errorMessage }}</span>
      <span v-else-if="chatStore.isRecording" class="voice-status recording">
        <span class="rec-dot" />正在聆听…
      </span>
      <span v-else class="voice-status">点击麦克风说话</span>
    </div>
  </div>
</template>

<style scoped>
.voice-control {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  flex: 1;
}

/* ============== 大圆麦克风按钮 ============== */
.voice-btn {
  position: relative;
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background: var(--color-surface-2);
  color: var(--brand-600);
  border: 2px solid var(--color-border-2);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all var(--t-normal) var(--ease-out);
}

.voice-btn:hover:not(:disabled) {
  border-color: var(--brand-400);
  background: var(--color-surface);
  transform: scale(1.05);
}

.voice-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.mic-core {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 录音状态：渐变 + 方形停止 + 三圈呼吸 */
.voice-btn.recording {
  background: var(--gradient-brand);
  color: #fff;
  border-color: transparent;
  box-shadow: 0 0 0 0 rgba(99, 102, 241, 0.5);
  animation: pulse-bg 1.6s ease-out infinite;
}

@keyframes pulse-bg {
  0% { box-shadow: 0 0 0 0 rgba(99, 102, 241, 0.45); }
  100% { box-shadow: 0 0 0 18px rgba(99, 102, 241, 0); }
}

.rec-square {
  width: 14px;
  height: 14px;
  background: #fff;
  border-radius: 3px;
}

/* 三层呼吸光环（始终渲染，录音态激活） */
.ring {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  border: 2px solid var(--brand-400);
  opacity: 0;
  pointer-events: none;
}

.voice-btn.recording .ring {
  animation: ring-pulse 1.8s ease-out infinite;
}
.voice-btn.recording .ring-2 { animation-delay: 0.3s; }
.voice-btn.recording .ring-3 { animation-delay: 0.6s; }

@keyframes ring-pulse {
  0% { transform: scale(1); opacity: 0.7; }
  100% { transform: scale(1.7); opacity: 0; }
}

/* ============== 文字说明 ============== */
.voice-text {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  flex: 1;
}

.voice-status {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--color-text-3);
}

.voice-status.recording {
  color: var(--brand-600);
  font-weight: 500;
}

.rec-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--color-danger);
  animation: blink 1s ease-in-out infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.4; transform: scale(0.7); }
}

.voice-error {
  color: var(--color-danger);
  font-size: 12px;
}
</style>

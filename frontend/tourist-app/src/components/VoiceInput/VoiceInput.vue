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
      class="voice-btn"
      :class="{ recording: chatStore.isRecording }"
      @click="toggleRecording"
      :disabled="chatStore.isLoading || !isSupported"
    >
      <svg
        v-if="!chatStore.isRecording"
        width="24" height="24" viewBox="0 0 24 24" fill="none"
        stroke="currentColor" stroke-width="2"
      >
        <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
        <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
        <line x1="12" y1="19" x2="12" y2="23" />
        <line x1="8" y1="23" x2="16" y2="23" />
      </svg>
      <span v-else class="recording-indicator">
        <span class="rec-dot"></span>
        正在聆听...
      </span>
    </button>
    <span class="voice-mode">浏览器实时 ASR</span>
    <span v-if="errorMessage" class="voice-error">{{ errorMessage }}</span>
  </div>
</template>

<style scoped>
.voice-control {
  display: flex;
  align-items: center;
  gap: 10px;
}

.voice-btn {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  border: 2px solid #d1d5db;
  background: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #6b7280;
  transition: all 0.2s;
}

.voice-btn:hover:not(:disabled) {
  border-color: #4f46e5;
  color: #4f46e5;
}

.voice-btn.recording {
  width: auto;
  border-radius: 24px;
  padding: 0 16px;
  background: #ef4444;
  border-color: #ef4444;
  color: white;
}

.recording-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  white-space: nowrap;
}

.rec-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: white;
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.voice-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.voice-mode {
  color: #6b7280;
  font-size: 12px;
}

.voice-error {
  color: #dc2626;
  font-size: 12px;
}
</style>

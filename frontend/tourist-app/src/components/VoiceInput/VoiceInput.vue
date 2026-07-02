<script setup lang="ts">
import { ref } from 'vue'
import { useChatStore } from '../../stores/chat'

const chatStore = useChatStore()
const mediaRecorder = ref<MediaRecorder | null>(null)
const audioChunks = ref<Blob[]>([])

const emit = defineEmits<{
  audioReady: [audio: Blob]
}>()

async function startRecording() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    mediaRecorder.value = new MediaRecorder(stream)
    audioChunks.value = []

    mediaRecorder.value.ondataavailable = (e) => {
      if (e.data.size > 0) {
        audioChunks.value.push(e.data)
      }
    }

    mediaRecorder.value.onstop = () => {
      const audioBlob = new Blob(audioChunks.value, { type: 'audio/webm' })
      emit('audioReady', audioBlob)
      stream.getTracks().forEach((t) => t.stop())
    }

    mediaRecorder.value.start()
    chatStore.setRecording(true)
  } catch {
    console.error('无法访问麦克风')
  }
}

function stopRecording() {
  if (mediaRecorder.value && mediaRecorder.value.state === 'recording') {
    mediaRecorder.value.stop()
    chatStore.setRecording(false)
  }
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
  <button
    class="voice-btn"
    :class="{ recording: chatStore.isRecording }"
    @click="toggleRecording"
    :disabled="chatStore.isLoading"
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
      录音中...
    </span>
  </button>
</template>

<style scoped>
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
</style>

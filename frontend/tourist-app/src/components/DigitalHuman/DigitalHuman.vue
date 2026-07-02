<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  emotion: string
  isSpeaking: boolean
  avatarUrl?: string
}>()

const emotionClass = computed(() => `emotion-${props.emotion}`)
const avatarSrc = computed(
  () => props.avatarUrl || '/avatar-default.png'
)
</script>

<template>
  <div class="digital-human" :class="[emotionClass, { speaking: isSpeaking }]">
    <div class="avatar-container">
      <div class="avatar-wrapper">
        <img :src="avatarSrc" alt="AI导游" class="avatar-image" />
        <div class="pulse-ring" v-if="isSpeaking"></div>
      </div>
      <div class="emotion-indicator">
        <span class="emotion-dot"></span>
        <span class="emotion-text">{{ emotionLabel }}</span>
      </div>
    </div>
    <div class="video-overlay" v-if="isSpeaking">
      <canvas ref="lipSyncCanvas" class="lip-sync-canvas"></canvas>
    </div>
  </div>
</template>

<script lang="ts">
export default {
  computed: {
    emotionLabel(): string {
      const labels: Record<string, string> = {
        neutral: '待命中',
        happy: '开心',
        explaining: '讲解中',
        caring: '关切',
        excited: '热情',
      }
      return labels[this.emotion] || '待命中'
    },
  },
}
</script>

<style scoped>
.digital-human {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  position: relative;
  overflow: hidden;
}

.avatar-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  z-index: 1;
}

.avatar-wrapper {
  position: relative;
  width: 200px;
  height: 200px;
}

.avatar-image {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
  border: 4px solid rgba(255, 255, 255, 0.3);
  transition: transform 0.3s ease;
}

.speaking .avatar-image {
  border-color: rgba(255, 255, 255, 0.8);
}

.pulse-ring {
  position: absolute;
  top: -10px;
  left: -10px;
  right: -10px;
  bottom: -10px;
  border-radius: 50%;
  border: 3px solid rgba(255, 255, 255, 0.4);
  animation: pulse 1.5s ease-out infinite;
}

@keyframes pulse {
  0% {
    transform: scale(1);
    opacity: 1;
  }
  100% {
    transform: scale(1.3);
    opacity: 0;
  }
}

.emotion-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 16px;
  padding: 6px 16px;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 20px;
  backdrop-filter: blur(10px);
}

.emotion-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #4ade80;
}

.emotion-text {
  color: white;
  font-size: 14px;
}

.emotion-happy .emotion-dot {
  background: #fbbf24;
}
.emotion-explaining .emotion-dot {
  background: #60a5fa;
}
.emotion-caring .emotion-dot {
  background: #f472b6;
}
.emotion-excited .emotion-dot {
  background: #fb923c;
}

.video-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
}

.lip-sync-canvas {
  width: 100%;
  height: 100%;
}
</style>

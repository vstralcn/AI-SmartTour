<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  emotion: string
  isSpeaking: boolean
  isThinking?: boolean
  avatarUrl?: string
  name?: string
  style?: string
  introduction?: string
}>()

const emotionClass = computed(() => `emotion-${props.emotion}`)
const avatarSrc = computed(
  () => props.avatarUrl || '/avatar-default.png'
)
const emotionLabel = computed(() => {
  const labels: Record<string, string> = {
    neutral: '待命中',
    happy: '开心',
    explaining: '讲解中',
    caring: '关切',
    excited: '热情',
  }
  if (props.isSpeaking) return '正在播报'
  if (props.isThinking) return '正在思考'
  return labels[props.emotion] || '待命中'
})
</script>

<template>
  <div class="digital-human" :class="[emotionClass, { speaking: isSpeaking }]">
    <div class="avatar-container">
      <div class="avatar-wrapper">
        <img :src="avatarSrc" alt="AI导游" class="avatar-image" />
        <span v-if="isSpeaking" class="animated-mouth"></span>
        <div class="pulse-ring" v-if="isSpeaking"></div>
      </div>
      <div class="guide-profile">
        <strong>{{ name || 'AI 导游' }}</strong>
        <span>{{ style || '智慧景区讲解员' }}</span>
      </div>
      <div class="emotion-indicator">
        <span class="emotion-dot"></span>
        <span class="emotion-text">{{ emotionLabel }}</span>
      </div>
      <p class="introduction" v-if="introduction">{{ introduction }}</p>
    </div>
  </div>
</template>

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
  transform: scale(1.015);
}

.animated-mouth {
  position: absolute;
  left: 50%;
  bottom: 39%;
  width: 24px;
  height: 6px;
  transform: translateX(-50%);
  border-radius: 50%;
  background: rgba(91, 33, 48, 0.76);
  box-shadow: 0 0 5px rgba(255, 255, 255, 0.35);
  animation: mouth-talk 0.28s ease-in-out infinite alternate;
}

@keyframes mouth-talk {
  from {
    height: 4px;
    width: 22px;
  }
  to {
    height: 13px;
    width: 18px;
  }
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

.guide-profile {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-top: 14px;
  color: white;
}

.guide-profile strong {
  font-size: 18px;
}

.guide-profile span {
  margin-top: 3px;
  font-size: 12px;
  opacity: 0.78;
}

.introduction {
  max-width: 320px;
  margin: 12px 24px 0;
  color: rgba(255, 255, 255, 0.82);
  font-size: 12px;
  line-height: 1.5;
  text-align: center;
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

</style>

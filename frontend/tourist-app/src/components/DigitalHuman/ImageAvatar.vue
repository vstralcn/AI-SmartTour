<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'

const props = defineProps<{
  emotion: string
  isSpeaking: boolean
  isThinking?: boolean
  avatarUrl?: string
}>()

const avatarSrc = computed(() => props.avatarUrl || '/avatar-default.png')

const particles = ref<
  { id: number; x: number; y: number; size: number; delay: number; duration: number }[]
>([])

onMounted(() => {
  const items = []
  for (let i = 0; i < 12; i++) {
    items.push({
      id: i,
      x: Math.random() * 100,
      y: Math.random() * 100,
      size: 2 + Math.random() * 3,
      delay: Math.random() * 8,
      duration: 3 + Math.random() * 4,
    })
  }
  particles.value = items
})

const emotionFilter = computed(() => {
  const map: Record<string, string> = {
    neutral: 'none',
    happy: 'brightness(1.06) saturate(1.08)',
    explaining: 'brightness(1.02) contrast(1.03)',
    caring: 'brightness(1.04) saturate(0.95)',
    excited: 'brightness(1.08) saturate(1.12) contrast(1.04)',
  }
  return map[props.emotion] || 'none'
})

const accentColor = computed(() => {
  const map: Record<string, string> = {
    neutral: '#7c6cf0',
    happy: '#f472b6',
    explaining: '#60a5fa',
    caring: '#fb923c',
    excited: '#f87171',
  }
  return map[props.emotion] || map.neutral
})
</script>

<template>
  <div class="image-avatar" :class="{ speaking: isSpeaking, thinking: isThinking }">
    <div class="particles-bg">
      <span
        v-for="p in particles"
        :key="p.id"
        class="particle"
        :style="{
          left: p.x + '%',
          top: p.y + '%',
          width: p.size + 'px',
          height: p.size + 'px',
          animationDelay: p.delay + 's',
          animationDuration: p.duration + 's',
          background: accentColor,
        }"
      />
    </div>

    <div class="avatar-wrapper">
      <svg class="orbit-ring orbit-ring-1" viewBox="0 0 100 100">
        <circle
          cx="50" cy="50" r="46"
          fill="none"
          :stroke="accentColor"
          stroke-width="0.6"
          stroke-dasharray="8 6"
          opacity="0.35"
        />
        <circle cx="50" cy="4" r="2.5" :fill="accentColor" opacity="0.6" />
      </svg>

      <svg class="orbit-ring orbit-ring-2" viewBox="0 0 100 100">
        <circle
          cx="50" cy="50" r="49"
          fill="none"
          :stroke="accentColor"
          stroke-width="0.3"
          stroke-dasharray="3 10"
          opacity="0.25"
        />
        <circle cx="50" cy="99" r="1.8" :fill="accentColor" opacity="0.5" />
      </svg>

      <div class="scan-line" />

      <img :src="avatarSrc" alt="AI导游" class="avatar-image" :style="{ filter: emotionFilter }" />

      <div class="corner-brackets">
        <span class="bracket tl" />
        <span class="bracket tr" />
        <span class="bracket bl" />
        <span class="bracket br" />
      </div>

      <div class="voice-waves" v-if="isSpeaking">
        <span
          v-for="i in 5"
          :key="i"
          class="wave-bar"
          :style="{
            background: accentColor,
            animationDelay: i * 0.12 + 's',
          }"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.image-avatar {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.particles-bg {
  position: absolute;
  inset: -40px;
  pointer-events: none;
  z-index: 0;
}

.particle {
  position: absolute;
  border-radius: 50%;
  opacity: 0;
  animation: particle-float 4s ease-in-out infinite;
}

@keyframes particle-float {
  0%, 100% {
    opacity: 0;
    transform: translateY(0) scale(0.5);
  }
  25% {
    opacity: 0.5;
  }
  50% {
    opacity: 0.2;
    transform: translateY(-40px) scale(1);
  }
  75% {
    opacity: 0.4;
  }
}

.avatar-wrapper {
  position: relative;
  width: 200px;
  height: 200px;
  animation: breathe 4s ease-in-out infinite;
}

.orbit-ring {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.orbit-ring-1 {
  animation: spin-cw 8s linear infinite;
}

.orbit-ring-2 {
  animation: spin-ccw 12s linear infinite;
}

.speaking .orbit-ring-1 {
  animation-duration: 4s;
}

.speaking .orbit-ring-2 {
  animation-duration: 6s;
}

@keyframes spin-cw {
  to {
    transform: rotate(360deg);
  }
}

@keyframes spin-ccw {
  to {
    transform: rotate(-360deg);
  }
}

.scan-line {
  position: absolute;
  left: 0;
  width: 100%;
  height: 3px;
  background: linear-gradient(90deg, transparent 0%, v-bind(accentColor) 50%, transparent 100%);
  opacity: 0;
  pointer-events: none;
  border-radius: 2px;
  animation: scan-line 4s ease-in-out infinite;
  filter: blur(1px);
}

@keyframes scan-line {
  0% {
    top: 0%;
    opacity: 0;
  }
  5% {
    opacity: 0.35;
  }
  45% {
    opacity: 0.35;
  }
  50% {
    opacity: 0;
  }
  55% {
    top: 100%;
    opacity: 0.35;
    transform: translateY(-3px);
  }
  95% {
    opacity: 0.35;
  }
  100% {
    top: 100%;
    opacity: 0;
    transform: translateY(-3px);
  }
}

.avatar-image {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
  box-shadow:
    0 0 30px v-bind(accentColor),
    inset 0 0 20px rgba(0, 0, 0, 0.3);
  transition:
    transform 0.3s ease,
    filter 0.6s ease,
    box-shadow 0.6s ease;
  will-change: transform, filter;
  position: relative;
  z-index: 2;
}

.speaking .avatar-image {
  animation: head-bob 0.6s ease-in-out infinite alternate;
}

.corner-brackets {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 3;
}

.bracket {
  position: absolute;
  display: block;
  width: 14px;
  height: 14px;
  border-color: v-bind(accentColor);
  opacity: 0.45;
}

.tl {
  top: 6px;
  left: 6px;
  border-top: 2px solid;
  border-left: 2px solid;
}

.tr {
  top: 6px;
  right: 6px;
  border-top: 2px solid;
  border-right: 2px solid;
}

.bl {
  bottom: 6px;
  left: 6px;
  border-bottom: 2px solid;
  border-left: 2px solid;
}

.br {
  bottom: 6px;
  right: 6px;
  border-bottom: 2px solid;
  border-right: 2px solid;
}

.voice-waves {
  position: absolute;
  bottom: -8px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: flex-end;
  gap: 3px;
  height: 16px;
  z-index: 3;
}

.wave-bar {
  width: 3px;
  border-radius: 2px;
  opacity: 0.7;
  animation: wave 0.5s ease-in-out infinite alternate;
}

.wave-bar:nth-child(1) { height: 6px; }
.wave-bar:nth-child(2) { height: 10px; }
.wave-bar:nth-child(3) { height: 14px; }
.wave-bar:nth-child(4) { height: 10px; }
.wave-bar:nth-child(5) { height: 6px; }

@keyframes wave {
  0% {
    transform: scaleY(0.5);
    opacity: 0.4;
  }
  100% {
    transform: scaleY(1.2);
    opacity: 0.9;
  }
}

@keyframes breathe {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.008);
  }
}

@keyframes head-bob {
  0% {
    transform: rotate(-0.4deg);
  }
  100% {
    transform: rotate(0.4deg);
  }
}
</style>

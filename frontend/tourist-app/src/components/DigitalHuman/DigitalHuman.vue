<script setup lang="ts">
import { computed, ref } from 'vue'
import ImageAvatar from './ImageAvatar.vue'
import VrmAvatar from './VrmAvatar.vue'

const props = withDefaults(
  defineProps<{
    emotion: string
    isSpeaking: boolean
    isThinking?: boolean
    avatarUrl?: string
    name?: string
    style?: string
    introduction?: string
    /** 高清播报视频地址，存在时切换为视频播报模式 */
    videoUrl?: string
    /** 视频是否静音（模拟引擎生成的视频无音轨，由浏览器 TTS 发声） */
    videoMuted?: boolean
    /** 3D VRM 模型地址；置空则直接使用贴图模式 */
    modelUrl?: string
    /** 语音词边界脉冲计数，用于驱动 3D 口型重读 */
    speechPulse?: number
  }>(),
  { videoUrl: '', videoMuted: true, modelUrl: '/models/guide.vrm', speechPulse: 0 }
)

const emit = defineEmits<{
  'video-ended': []
}>()

/** VRM 加载失败标记 —— 失败后降级为贴图模式 */
const vrmFailed = ref(false)

const stageMode = computed<'video' | 'vrm' | 'image'>(() => {
  if (props.videoUrl) return 'video'
  if (props.modelUrl && !vrmFailed.value) return 'vrm'
  return 'image'
})

const emotionLabel = computed(() => {
  const labels: Record<string, string> = {
    neutral: '待命中',
    happy: '开心',
    explaining: '讲解中',
    caring: '关切',
    excited: '热情',
  }
  if (props.videoUrl) return '高清播报中'
  if (props.isSpeaking) return '正在播报'
  if (props.isThinking) return '正在思考'
  return labels[props.emotion] || '待命中'
})

const bgGradient = computed(() => {
  const map: Record<string, string> = {
    neutral: 'linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%)',
    happy: 'linear-gradient(135deg, #1a0533 0%, #4a1a6b 50%, #2d1b4e 100%)',
    explaining: 'linear-gradient(135deg, #0a1628 0%, #1a3a5c 50%, #0f1f3a 100%)',
    caring: 'linear-gradient(135deg, #2a0a1e 0%, #5c1a3a 50%, #3a0f28 100%)',
    excited: 'linear-gradient(135deg, #1a0a05 0%, #5c2a1a 50%, #3a1a0f 100%)',
  }
  return map[props.emotion] || map.neutral
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

function onVrmError(reason: string) {
  console.warn(`VRM 模式不可用，已降级为贴图模式：${reason}`)
  vrmFailed.value = true
}
</script>

<template>
  <div
    class="digital-human"
    :class="[`stage-${stageMode}`, { speaking: isSpeaking, thinking: isThinking }]"
    :style="{ background: bgGradient }"
  >
    <div class="avatar-container">
      <div class="stage" :style="{ borderColor: accentColor }">
        <!-- 高清播报视频 -->
        <template v-if="stageMode === 'video'">
          <video
            class="broadcast-video"
            :src="videoUrl"
            :muted="videoMuted"
            autoplay
            playsinline
            @ended="emit('video-ended')"
          />
          <span class="broadcast-badge">HD</span>
        </template>

        <!-- 3D VRM 实时互动 -->
        <VrmAvatar
          v-else-if="stageMode === 'vrm'"
          :emotion="emotion"
          :is-speaking="isSpeaking"
          :is-thinking="isThinking"
          :model-url="modelUrl"
          :speech-pulse="speechPulse"
          @error="onVrmError"
        />

        <!-- 贴图降级模式 -->
        <ImageAvatar
          v-else
          :emotion="emotion"
          :is-speaking="isSpeaking"
          :is-thinking="isThinking"
          :avatar-url="avatarUrl"
        />
      </div>

      <div class="guide-profile">
        <strong>{{ name || 'AI 导游' }}</strong>
        <span>{{ style || '智慧景区讲解员' }}</span>
      </div>

      <div class="emotion-indicator">
        <span class="emotion-dot" :style="{ background: accentColor }" />
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
  border-radius: 16px;
  position: relative;
  overflow: hidden;
  transition: background 0.8s ease;
}

.avatar-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  z-index: 1;
  width: 100%;
  max-width: 380px;
}

/* 数字人舞台：三种模式共用 */
.stage {
  position: relative;
  width: 100%;
  height: 320px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stage-image {
  height: 220px;
}

.broadcast-video {
  width: 100%;
  height: 100%;
  object-fit: contain;
  border-radius: 12px;
  background: rgba(0, 0, 0, 0.35);
}

.broadcast-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.5px;
  color: #fff;
  background: linear-gradient(135deg, #f59e0b, #ef4444);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.35);
}

.emotion-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 12px;
  padding: 4px 14px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  backdrop-filter: blur(10px);
  transition: border-color 0.4s ease;
}

.guide-profile {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-top: 12px;
  color: white;
}

.guide-profile strong {
  font-size: 18px;
  text-shadow: 0 0 20px rgba(255, 255, 255, 0.15);
}

.guide-profile span {
  margin-top: 3px;
  font-size: 12px;
  opacity: 0.65;
}

.introduction {
  max-width: 320px;
  margin: 8px 24px 0;
  color: rgba(255, 255, 255, 0.65);
  font-size: 12px;
  line-height: 1.5;
  text-align: center;
}

.emotion-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  box-shadow: 0 0 8px currentColor;
  transition: background 0.4s ease;
}

.emotion-text {
  color: rgba(255, 255, 255, 0.85);
  font-size: 13px;
}
</style>

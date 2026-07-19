<script setup lang="ts">
import { computed, ref } from 'vue'
import ImageAvatar from './ImageAvatar.vue'
import VrmAvatar from './VrmAvatar.vue'
import XunfeiAvatar from './XunfeiAvatar.vue'

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
    /** 启用讯飞虚拟人实时模式 */
    enableXunfei?: boolean
    /** 讯飞待播报文本 */
    xunfeiText?: string
    /** 讯飞驱动序号：自增触发一次播报 */
    xunfeiSeq?: number
  }>(),
  {
    videoUrl: '',
    videoMuted: true,
    modelUrl: '/models/guide.vrm',
    speechPulse: 0,
    enableXunfei: false,
    xunfeiText: '',
    xunfeiSeq: 0,
  }
)

const emit = defineEmits<{
  'video-ended': []
  /** 讯飞不可用（未配置/启动失败），父级据此回退实时模式 */
  'xunfei-error': [reason: string]
  /** 讯飞播报状态变化 */
  'xunfei-speaking': [value: boolean]
}>()

/** VRM 加载失败标记 —— 失败后降级为贴图模式 */
const vrmFailed = ref(false)
/** 讯飞不可用标记 —— 失败后降级为 VRM */
const xunfeiFailed = ref(false)

const stageMode = computed<'video' | 'xunfei' | 'vrm' | 'image'>(() => {
  if (props.videoUrl) return 'video'
  if (props.enableXunfei && !xunfeiFailed.value) return 'xunfei'
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

const emotionEmoji = computed(() => {
  const map: Record<string, string> = {
    neutral: '✨',
    happy: '😊',
    explaining: '🗣️',
    caring: '🤗',
    excited: '🤩',
  }
  if (props.videoUrl) return '🎬'
  if (props.isSpeaking) return '🗨️'
  if (props.isThinking) return '💭'
  return map[props.emotion] || '✨'
})

function onVrmError(reason: string) {
  console.warn(`VRM 模式不可用，已降级为贴图模式：${reason}`)
  vrmFailed.value = true
}

function onXunfeiError(reason: string) {
  xunfeiFailed.value = true
  emit('xunfei-error', reason)
}
</script>

<template>
  <div
    class="digital-human"
    :class="[`stage-${stageMode}`, { speaking: isSpeaking, thinking: isThinking }]"
  >
    <!-- 圆形光晕背景 -->
    <div class="halo" :style="{ '--accent': accentColor }" />

    <div class="avatar-card">
      <div class="stage" :style="{ '--accent': accentColor }">
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

        <!-- 讯飞虚拟人实时互动 -->
        <XunfeiAvatar
          v-else-if="stageMode === 'xunfei'"
          :drive-text="xunfeiText"
          :drive-seq="xunfeiSeq"
          @error="onXunfeiError"
          @speaking="(v) => emit('xunfei-speaking', v)"
        />

        <!-- 3D VRM 实时互动 -->
        <VrmAvatar
          v-else-if="stageMode === 'vrm'"
          :emotion="emotion"
          :is-speaking="isSpeaking"
          :is-thinking="isThinking"
          :model-url="modelUrl"
          :speech-pulse="speech-pulse"
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

      <!-- 名称 + 状态 -->
      <div class="guide-meta">
        <div class="guide-name-row">
          <strong class="guide-name">{{ name || 'AI 导游' }}</strong>
          <span class="guide-style">{{ style || '智慧景区讲解员' }}</span>
        </div>
        <div class="emotion-chip" :style="{ '--accent': accentColor }">
          <span class="emotion-dot" />
          <span class="emotion-emoji">{{ emotionEmoji }}</span>
          <span class="emotion-text">{{ emotionLabel }}</span>
        </div>
        <p v-if="introduction" class="introduction">{{ introduction }}</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* ============== 容器 ============== */
.digital-human {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
  height: 100%;
  border-radius: var(--r-2xl);
  overflow: hidden;
  background: var(--color-surface);
  box-shadow: var(--shadow-md);
  padding: var(--sp-5) var(--sp-4) var(--sp-4);
  transition: box-shadow var(--t-slow) var(--ease-out);
}

.digital-human.speaking {
  box-shadow: 0 8px 32px rgba(99, 102, 241, 0.18);
}

.halo {
  position: absolute;
  top: 12%;
  left: 50%;
  transform: translateX(-50%);
  width: 280px;
  height: 280px;
  border-radius: 50%;
  background: radial-gradient(
    circle at center,
    var(--accent) 0%,
    transparent 70%
  );
  opacity: 0.18;
  filter: blur(40px);
  pointer-events: none;
  transition: opacity var(--t-slow) var(--ease-out);
  z-index: 0;
}

.speaking .halo {
  opacity: 0.32;
}

/* ============== 舞台卡 ============== */
.avatar-card {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  max-width: 420px;
  flex: 1;
  min-height: 0;
}

.stage {
  position: relative;
  width: 100%;
  flex: 1;
  min-height: 320px;
  max-height: 480px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--r-2xl);
  overflow: hidden;
  background: linear-gradient(180deg, #1a1b3a 0%, #0f0f24 100%);
  box-shadow:
    inset 0 0 0 1px rgba(255, 255, 255, 0.06),
    0 8px 24px rgba(15, 15, 36, 0.3);
  --accent: #7c6cf0;
}

.stage::after {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: inherit;
  pointer-events: none;
  box-shadow: inset 0 -40px 60px -20px rgba(124, 108, 240, 0.18);
}

.broadcast-video {
  width: 100%;
  height: 100%;
  object-fit: contain;
  border-radius: var(--r-2xl);
}

.broadcast-badge {
  position: absolute;
  top: 12px;
  right: 12px;
  padding: 4px 10px;
  border-radius: var(--r-pill);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.5px;
  color: #fff;
  background: linear-gradient(135deg, #f59e0b, #ef4444);
  box-shadow: 0 2px 12px rgba(245, 158, 11, 0.4);
  z-index: 2;
}

/* ============== 名称 + 状态 ============== */
.guide-meta {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--sp-2);
  width: 100%;
  margin-top: var(--sp-4);
  text-align: center;
}

.guide-name-row {
  display: flex;
  align-items: baseline;
  gap: var(--sp-2);
  flex-wrap: wrap;
  justify-content: center;
}
.guide-name {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text);
}
.guide-style {
  font-size: 12px;
  color: var(--color-text-3);
}

.emotion-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 12px;
  background: var(--color-surface-2);
  border: 1px solid var(--color-border-2);
  border-radius: var(--r-pill);
  font-size: 12px;
  color: var(--color-text-2);
  --accent: #7c6cf0;
}

.emotion-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--accent);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent) 20%, transparent);
  animation: pulse 1.8s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.emotion-emoji {
  font-size: 13px;
  line-height: 1;
}

.introduction {
  max-width: 320px;
  margin-top: 2px;
  color: var(--color-text-3);
  font-size: 12px;
  line-height: 1.6;
}
</style>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { fetchXunfeiSignedInfo } from '../../services/api'

const props = withDefaults(
  defineProps<{
    /** 待播报文本 */
    driveText?: string
    /** 驱动序号：每次自增触发一次 writeText */
    driveSeq?: number
  }>(),
  { driveText: '', driveSeq: 0 }
)

const emit = defineEmits<{
  /** 连接并拉流成功 */
  ready: []
  /** 未配置 / 初始化失败：父组件据此降级回 VRM */
  error: [reason: string]
  /** 播报状态变化，用于同步 UI */
  speaking: [value: boolean]
}>()

/** SDK ESM 部署在静态目录，动态加载避免进入打包、保持播放器分包同目录解析 */
const SDK_URL = '/sdk/avatar-sdk-web_3.2.3.1002/esm/index.js'

const wrapperRef = ref<HTMLDivElement | null>(null)
const status = ref<'connecting' | 'ready' | 'failed'>('connecting')
const statusText = ref('讯飞数字人连接中…')

// 非响应式：AvatarPlatform 实例不可放进 ref/reactive，否则代理破坏其私有成员
let avatar: any = null
let ready = false
let destroyed = false
/** 就绪前到达的文本先缓存，连接成功后补播 */
let pendingText = ''

async function init() {
  try {
    statusText.value = '正在拉取讯飞接入参数…'
    const info = await fetchXunfeiSignedInfo()
    if (destroyed) return
    if (!info.enabled || !info.signedUrl) {
      fail('讯飞虚拟人未配置')
      return
    }

    statusText.value = '正在加载讯飞 SDK…'
    const mod: any = await import(/* @vite-ignore */ SDK_URL)
    if (destroyed) return
    const AvatarPlatform = mod.default
    const { SDKEvents, PlayerEvents } = mod

    // useInlinePlayer=true：让 SDK 内部创建并管理 Player，
    // start() 时自动把视频流挂载到 wrapper 并调用 playStream。
    // 不传则 SDK 不会创建 Player，视频流无法显示（数字人黑屏的根因之一）。
    avatar = new AvatarPlatform({ useInlinePlayer: true })
    bindEvents(SDKEvents, PlayerEvents)

    // 安全接入：仅传 appId + sceneId + signedUrl，密钥不出现在前端
    avatar.setApiInfo({
      appId: info.appId,
      sceneId: info.sceneId,
      signedUrl: info.signedUrl,
    })
    avatar.setGlobalParams({
      stream: { protocol: 'xrtc' }, // 首版不开透明背景，跑通后再加 alpha:1
      avatar: { avatar_id: info.avatarId, width: 720, height: 1280 }, // 宽高须为 4 的倍数
      tts: { vcn: info.vcn },
    })

    statusText.value = '正在与讯飞服务器握手…'
    await avatar.start({ wrapper: wrapperRef.value! })
    if (destroyed) {
      teardown()
      return
    }
    ready = true
    status.value = 'ready'
    emit('ready')
    if (pendingText) {
      const text = pendingText
      pendingText = ''
      void drive(text)
    }
  } catch (e: any) {
    fail(`讯飞启动失败：${e?.code ?? ''} ${e?.message ?? e}`)
  }
}

function bindEvents(SDKEvents: any, PlayerEvents: any) {
  avatar
    .on(SDKEvents.connected, () => {
      console.info('[讯飞] 已连接，开始拉流')
      statusText.value = '已连接，等待视频流…'
    })
    .on(SDKEvents.stream_start, () => {
      console.info('[讯飞] 视频流开始')
      status.value = 'ready'
    })
    .on(SDKEvents.frame_start, () => emit('speaking', true))
    .on(SDKEvents.frame_stop, () => emit('speaking', false))
    .on(SDKEvents.disconnected, (err: any) => {
      emit('speaking', false)
      if (err) fail(`讯飞异常断开：${err?.code ?? ''} ${err?.message ?? ''}`)
    })
    .on(SDKEvents.error, (err: any) =>
      console.warn('[讯飞] error', err?.code, err?.message)
    )

  // 浏览器自动播放限制：需用户交互后 resume() 恢复声音。
  // useInlinePlayer=true 时构造函数已创建 player，这里直接取。
  const player = avatar.player || avatar.createPlayer()
  player.on(PlayerEvents.playNotAllowed, () => {
    console.warn('[讯飞] 浏览器阻止自动播放，等待用户点击后恢复')
    const resume = () => {
      avatar?.player?.resume?.()
      document.removeEventListener('click', resume)
    }
    document.addEventListener('click', resume)
  })
  player.on(PlayerEvents.error, (err: any) =>
    console.warn('[讯飞] player error', err?.code, err?.message)
  )
}

/** 文本驱动：新回复先打断当前播报，再纯播报（nlp:false，文本由本项目 Agent 产出） */
async function drive(text: string) {
  const t = text.trim()
  if (!t || !ready || !avatar) return
  try {
    await avatar.interrupt().catch(() => {})
    await avatar.writeText(t, { nlp: false })
  } catch (e: any) {
    console.warn('[讯飞] writeText 失败', e?.code, e?.message)
  }
}

function fail(reason: string) {
  if (status.value === 'failed') return
  status.value = 'failed'
  statusText.value = reason
  console.warn(`[讯飞] ${reason}，降级回 VRM`)
  teardown()
  emit('error', reason)
}

function teardown() {
  try {
    avatar?.stop()
  } catch {}
  try {
    avatar?.destroy()
  } catch {}
  avatar = null
  ready = false
}

watch(
  () => props.driveSeq,
  () => {
    const text = props.driveText
    if (!text) return
    if (ready) void drive(text)
    else pendingText = text // 就绪后补播
  }
)

onMounted(() => {
  if (props.driveText) pendingText = props.driveText
  void init()
})

onBeforeUnmount(() => {
  destroyed = true
  teardown()
})
</script>

<template>
  <div class="xunfei-avatar">
    <!-- SDK Player 挂载点：内部由 SDK 插入 <video>/<canvas> 等媒体元素 -->
    <div ref="wrapperRef" class="xunfei-wrapper" />

    <!-- 加载提示层（仅 connecting 时显示） -->
    <div v-if="status === 'connecting'" class="xunfei-overlay">
      <div class="spinner" />
      <span class="overlay-text">{{ statusText }}</span>
    </div>

    <!-- 失败提示层 -->
    <div v-else-if="status === 'failed'" class="xunfei-overlay xunfei-failed">
      <span class="fail-icon">⚠</span>
      <span class="overlay-text">{{ statusText }}</span>
    </div>

    <!-- 右上角"讯飞"徽章：就绪后展示 -->
    <span v-if="status === 'ready'" class="xunfei-badge">
      <span class="live-dot" />
      讯飞
    </span>
  </div>
</template>

<style scoped>
.xunfei-avatar {
  position: relative;
  width: 100%;
  height: 100%;
  flex: 1;
  min-height: 0;
  border-radius: inherit;
  overflow: hidden;
}

/* ===== 关键：wrapper 占满父容器，强制内部 video/canvas fill ===== */
.xunfei-wrapper {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  border-radius: inherit;
  overflow: hidden;
  background: linear-gradient(135deg, #1a1b3a 0%, #0f0f24 100%);
}

.xunfei-wrapper :deep(video),
.xunfei-wrapper :deep(canvas) {
  width: 100% !important;
  height: 100% !important;
  object-fit: contain;
  display: block;
}

/* ===== 加载/失败遮罩 ===== */
.xunfei-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  background: rgba(15, 15, 36, 0.55);
  backdrop-filter: blur(8px);
  color: rgba(255, 255, 255, 0.85);
  z-index: 2;
  pointer-events: none;
}

.xunfei-failed {
  background: rgba(239, 68, 68, 0.12);
  color: #fca5a5;
}

.spinner {
  width: 36px;
  height: 36px;
  border: 3px solid rgba(255, 255, 255, 0.15);
  border-top-color: #8b5cf6;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.fail-icon {
  font-size: 32px;
  color: #fca5a5;
}

.overlay-text {
  font-size: 12px;
  letter-spacing: 0.3px;
  text-align: center;
  padding: 0 16px;
}

/* ===== 右上"讯飞"徽章 ===== */
.xunfei-badge {
  position: absolute;
  top: 12px;
  right: 12px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: var(--r-pill);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.5px;
  color: #fff;
  background: linear-gradient(135deg, #6366f1, #a855f7);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
  z-index: 3;
}

.live-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #10b981;
  box-shadow: 0 0 6px #10b981;
  animation: pulse 1.4s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.6; transform: scale(0.85); }
}
</style>

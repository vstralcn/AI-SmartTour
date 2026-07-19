import api from './api'

export interface SpeechVoiceConfig {
  voice_id: string
  speed: number
  pitch: number
}

interface SpeechCallbacks {
  onStart: () => void
  onEnd: () => void
  /** 播报过程中周期性触发，用于驱动数字人口型重读脉冲 */
  onBoundary?: () => void
}

/** 当前后端音频播放实例 */
let currentAudio: HTMLAudioElement | null = null
/** 后端音频播放期间的口型脉冲定时器 */
let boundaryTimer: number | null = null

function startBoundaryPulse(callbacks: SpeechCallbacks) {
  if (!callbacks.onBoundary) return
  stopBoundaryPulse()
  boundaryTimer = window.setInterval(() => callbacks.onBoundary?.(), 180)
}

function stopBoundaryPulse() {
  if (boundaryTimer !== null) {
    window.clearInterval(boundaryTimer)
    boundaryTimer = null
  }
}

/**
 * 播报文本：优先使用后端神经 TTS（自然度高、支持情感韵律），
 * 不可用时降级为浏览器 SpeechSynthesis，保证链路不中断。
 */
export async function speak(
  text: string,
  config: SpeechVoiceConfig,
  emotion: string,
  callbacks: SpeechCallbacks
): Promise<boolean> {
  if (!text.trim()) return false
  cancelSpeech()

  const backendOk = await speakViaBackend(text, config, emotion, callbacks)
  if (backendOk) return true

  return speakViaBrowser(text, config, callbacks)
}

/** 后端神经 TTS：拉取音频并播放 */
async function speakViaBackend(
  text: string,
  config: SpeechVoiceConfig,
  emotion: string,
  callbacks: SpeechCallbacks
): Promise<boolean> {
  let url = ''
  try {
    const { data } = await api.post(
      '/tts',
      {
        text,
        voice_id: config.voice_id,
        speed: config.speed,
        pitch: config.pitch,
        emotion,
      },
      { responseType: 'arraybuffer', timeout: 20000 }
    )
    const buffer = data as ArrayBuffer
    if (!buffer || buffer.byteLength === 0) return false

    const blob = new Blob([buffer], { type: 'audio/mpeg' })
    url = URL.createObjectURL(blob)
    const audio = new Audio(url)
    currentAudio = audio

    const cleanup = () => {
      stopBoundaryPulse()
      URL.revokeObjectURL(url)
      if (currentAudio === audio) currentAudio = null
    }
    audio.onplay = () => {
      callbacks.onStart()
      startBoundaryPulse(callbacks)
    }
    audio.onended = () => {
      cleanup()
      callbacks.onEnd()
    }
    audio.onerror = () => {
      cleanup()
      callbacks.onEnd()
    }

    await audio.play()
    return true
  } catch {
    // 503 / 网络失败 / 自动播放被拦截 —— 交给浏览器语音降级
    stopBoundaryPulse()
    if (url) URL.revokeObjectURL(url)
    currentAudio = null
    return false
  }
}

/** 浏览器 SpeechSynthesis 降级方案 */
function speakViaBrowser(
  text: string,
  config: SpeechVoiceConfig,
  callbacks: SpeechCallbacks
): boolean {
  if (!('speechSynthesis' in window)) {
    return false
  }

  window.speechSynthesis.cancel()
  const utterance = new SpeechSynthesisUtterance(text)
  const chineseVoices = window.speechSynthesis
    .getVoices()
    .filter((voice) => voice.lang.toLowerCase().startsWith('zh'))
  const preferredIndex = config.voice_id.startsWith('male') ? 1 : 0
  utterance.voice = chineseVoices[preferredIndex] || chineseVoices[0] || null
  utterance.lang = 'zh-CN'
  utterance.rate = Math.min(Math.max(config.speed, 0.5), 2)
  utterance.pitch = Math.min(Math.max(config.pitch, 0.5), 2)
  utterance.onstart = callbacks.onStart
  utterance.onend = callbacks.onEnd
  utterance.onerror = callbacks.onEnd
  if (callbacks.onBoundary) {
    utterance.onboundary = callbacks.onBoundary
  }
  window.speechSynthesis.speak(utterance)
  return true
}

export function cancelSpeech() {
  stopBoundaryPulse()
  if (currentAudio) {
    currentAudio.pause()
    currentAudio.src = ''
    currentAudio = null
  }
  if ('speechSynthesis' in window) {
    window.speechSynthesis.cancel()
  }
}

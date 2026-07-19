export interface SpeechVoiceConfig {
  voice_id: string
  speed: number
  pitch: number
}

interface SpeechCallbacks {
  onStart: () => void
  onEnd: () => void
  /** 朗读到每个词/字边界时触发，用于驱动数字人口型重读 */
  onBoundary?: () => void
}

export function speakText(
  text: string,
  config: SpeechVoiceConfig,
  callbacks: SpeechCallbacks
): boolean {
  if (!('speechSynthesis' in window) || !text.trim()) {
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
  if ('speechSynthesis' in window) {
    window.speechSynthesis.cancel()
  }
}

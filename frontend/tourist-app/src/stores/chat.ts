import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: number
  emotion?: string
  audioUrl?: string
}

export interface UserProfile {
  interests: string[]
  visitDuration: number
  physicalCondition: string
  visitedSpots: string[]
}

export const useChatStore = defineStore('chat', () => {
  const sessionId = ref<string>('')
  const messages = ref<ChatMessage[]>([])
  const isLoading = ref(false)
  const isRecording = ref(false)
  const currentEmotion = ref('neutral')
  const userProfile = ref<UserProfile>({
    interests: [],
    visitDuration: 3,
    physicalCondition: '正常',
    visitedSpots: [],
  })

  function addMessage(msg: ChatMessage) {
    messages.value.push(msg)
  }

  function setSessionId(id: string) {
    sessionId.value = id
  }

  function setLoading(val: boolean) {
    isLoading.value = val
  }

  function setRecording(val: boolean) {
    isRecording.value = val
  }

  function setEmotion(emotion: string) {
    currentEmotion.value = emotion
  }

  function clearMessages() {
    messages.value = []
  }

  return {
    sessionId,
    messages,
    isLoading,
    isRecording,
    currentEmotion,
    userProfile,
    addMessage,
    setSessionId,
    setLoading,
    setRecording,
    setEmotion,
    clearMessages,
  }
})

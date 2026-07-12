import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: number
  emotion?: string
  audioUrl?: string
  agentSteps?: AgentStep[]
  sources?: KnowledgeSource[]
}

export interface AgentStep {
  tool: string
  status: string
  detail: string
}

export interface KnowledgeSource {
  title: string
  category: string
  score: number
  source: string
}

export interface UserProfile {
  interests: string[]
  visitDuration: number
  ageGroup: string
  companions: string[]
  mobility: string
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
    ageGroup: '成人',
    companions: [],
    mobility: '标准',
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

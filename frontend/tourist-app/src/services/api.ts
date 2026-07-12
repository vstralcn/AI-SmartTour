import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE || ''

const api = axios.create({
  baseURL: `${API_BASE}/api/v1`,
  timeout: 30000,
})

export interface CreateSessionRequest {
  visitor_id?: string
  interests?: string[]
  age_group?: string
  companions?: string[]
  mobility?: string
  visit_duration?: number
}

export interface CreateSessionResponse {
  session_id: string
  greeting: string
}

export interface RouteRecommendRequest {
  session_id: string
  duration_hours: number
  interests: string[]
  companions: string[]
  mobility: string
}

export interface ScenicSpot {
  id: string
  name: string
  description: string
  category: string
  recommended_duration: number
  tags: string[]
}

export interface RouteRecommendResponse {
  route: ScenicSpot[]
  description: string
}

export interface AvatarConfig {
  id: string
  name: string
  appearance: {
    image_url: string
    style: string
  }
  voice_config: {
    voice_id: string
    speed: number
    pitch: number
  }
  personality: string
  gender: string
  clothing: string
  speaking_style: string
  is_active: boolean
}

export async function createSession(
  req: CreateSessionRequest
): Promise<CreateSessionResponse> {
  const { data } = await api.post('/sessions', req)
  return data
}

export async function getRecommendedRoute(
  req: RouteRecommendRequest
): Promise<RouteRecommendResponse> {
  const { data } = await api.post('/recommend/route', req)
  return data
}

export async function getActiveAvatar(): Promise<AvatarConfig> {
  const { data } = await api.get('/avatar/active')
  return data
}

export function createChatWebSocket(sessionId: string): WebSocket {
  const wsBase = API_BASE
    ? API_BASE.replace(/^http/, 'ws')
    : `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}`
  return new WebSocket(`${wsBase}/api/v1/chat/stream?session_id=${sessionId}`)
}

export default api

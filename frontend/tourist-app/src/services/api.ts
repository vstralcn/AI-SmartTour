import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

const api = axios.create({
  baseURL: `${API_BASE}/api/v1`,
  timeout: 30000,
})

export interface CreateSessionRequest {
  visitor_id?: string
  interests?: string[]
}

export interface CreateSessionResponse {
  session_id: string
  greeting: string
}

export interface RouteRecommendRequest {
  session_id: string
  duration_hours: number
  interests: string[]
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

export function createChatWebSocket(sessionId: string): WebSocket {
  const wsBase = API_BASE.replace(/^http/, 'ws')
  return new WebSocket(`${wsBase}/api/v1/chat/stream?session_id=${sessionId}`)
}

export default api

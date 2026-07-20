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

// ---- 数字人高清播报 ----

export interface BroadcastJob {
  job_id: string
  status: 'queued' | 'processing' | 'done' | 'failed'
  message?: string
  /** 视频是否自带音轨；模拟引擎生成的视频无音轨，前端需继续用浏览器 TTS 发声 */
  has_audio?: boolean
  /** 生成引擎：musetalk（GPU 真人口型同步）或 simulate（ffmpeg 模拟播报） */
  engine?: string
}

export async function requestBroadcast(
  text: string,
  emotion: string,
  imageUrl: string
): Promise<BroadcastJob> {
  const imageResp = await fetch(imageUrl)
  if (!imageResp.ok) {
    throw new Error('数字人形象图片获取失败')
  }
  const imageBlob = await imageResp.blob()
  const form = new FormData()
  form.append('text', text)
  form.append('emotion', emotion)
  form.append('image', imageBlob, 'avatar.png')
  const { data } = await api.post('/digital-human/broadcast', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 60000,
  })
  return data
}

export async function getBroadcastJob(jobId: string): Promise<BroadcastJob> {
  const { data } = await api.get(`/digital-human/broadcast/${jobId}`)
  return data
}

export function getBroadcastVideoUrl(jobId: string): string {
  return `${API_BASE}/api/v1/digital-human/broadcast/${jobId}/video`
}

// ---- 讯飞虚拟人 Web SDK ----

export interface XunfeiSignedInfo {
  enabled: boolean
  appId?: string
  sceneId?: string
  avatarId?: string
  vcn?: string
  /** 后端 HMAC-SHA256 签名后的完整 wss 地址，含时效，勿缓存 */
  signedUrl?: string
}

/** 拉取讯飞接入参数；未配置时后端返回 enabled=false，前端据此降级回 VRM。 */
export async function fetchXunfeiSignedInfo(sessionId: string): Promise<XunfeiSignedInfo> {
  const { data } = await api.get('/avatar/xunfei/signed-url', {
    params: { session_id: sessionId },
  })
  return data
}

export default api

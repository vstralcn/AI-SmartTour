import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE || ''

const api = axios.create({
  baseURL: `${API_BASE}/api/v1/admin`,
  timeout: 30000,
})

/* ---- Knowledge Base ---- */

export interface KnowledgeDoc {
  id: string
  title: string
  category: string
  content: string
  file_path: string
  upload_time: string
  status: string
  kind: string
  source: string
  keywords: string[]
  tags: string[]
}

export interface KnowledgeEntryInput {
  title: string
  category: string
  content: string
  kind: string
  source: string
  keywords: string[]
  tags: string[]
  status?: string
}

export async function listKnowledgeDocs(): Promise<KnowledgeDoc[]> {
  const { data } = await api.get('/knowledge/list')
  return data
}

export async function uploadKnowledgeDoc(formData: FormData): Promise<KnowledgeDoc> {
  const { data } = await api.post('/knowledge/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export async function createKnowledgeEntry(
  payload: KnowledgeEntryInput
): Promise<KnowledgeDoc> {
  const { data } = await api.post('/knowledge/entries', payload)
  return data
}

export async function updateKnowledgeEntry(
  id: string,
  payload: KnowledgeEntryInput
): Promise<KnowledgeDoc> {
  const { data } = await api.put(`/knowledge/${id}`, payload)
  return data
}

export async function deleteKnowledgeDoc(id: string): Promise<void> {
  await api.delete(`/knowledge/${id}`)
}

export interface KnowledgeEvidence {
  title: string
  category: string
  score: number
  source: string
  excerpt: string
}

export async function testKnowledge(question: string): Promise<{
  answer: string
  sources: string[]
  confidence: number
  evidence: KnowledgeEvidence[]
}> {
  const { data } = await api.post('/knowledge/test', { question })
  return data
}

/* ---- Avatar Config ---- */

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

export async function listAvatars(): Promise<AvatarConfig[]> {
  const { data } = await api.get('/avatar/list')
  return data
}

export async function saveAvatarConfig(config: Partial<AvatarConfig>): Promise<AvatarConfig> {
  const { data } = await api.post('/avatar/config', config)
  return data
}

export async function activateAvatar(id: string): Promise<void> {
  await api.put(`/avatar/${id}/activate`)
}

export async function deleteAvatar(id: string): Promise<void> {
  await api.delete(`/avatar/${id}`)
}

/* ---- Analytics ---- */

export interface DashboardData {
  today_visitors: number
  weekly_visitors: number
  total_sessions: number
  avg_response_ms: number
  knowledge_gap_count: number
  negative_feedback_count: number
  hot_questions: { question: string; count: number }[]
  response_time_trend: { date: string; value: number }[]
  hourly_visits: { hour: number; count: number }[]
  spot_popularity: { name: string; visits: number }[]
  route_preferences: { name: string; count: number }[]
  data_source: string
  generated_at: string
}

export async function getDashboardData(): Promise<DashboardData> {
  const { data } = await api.get('/analytics/dashboard')
  return data
}

export interface SentimentReport {
  positive_ratio: number
  neutral_ratio: number
  negative_ratio: number
  trend: { date: string; positive: number; neutral: number; negative: number }[]
  top_concerns: { topic: string; count: number; sentiment: string }[]
  suggestions: string[]
}

export async function getSentimentReport(): Promise<SentimentReport> {
  const { data } = await api.get('/analytics/sentiment')
  return data
}

export default api

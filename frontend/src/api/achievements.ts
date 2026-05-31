import type { Achievement } from '@/types/api'
import { requestJson } from './http'

const BASE = '/api/achievements'

export async function fetchAchievements(token: string): Promise<Achievement[]> {
  return requestJson<Achievement[]>(`${BASE}/`, {
    headers: { 'Authorization': `Bearer ${token}` }
  }, '加载成就列表失败。')
}

import type { LeaderboardResponse } from '@/types/api'
import { requestJson } from './http'

const BASE = '/api/leaderboard'

export async function fetchLeaderboard(token?: string | null, type = 'power', limit = 50): Promise<LeaderboardResponse> {
  return requestJson<LeaderboardResponse>(`${BASE}/?type=${type}&limit=${limit}`, {
    headers: token ? { 'Authorization': `Bearer ${token}` } : undefined,
  }, '加载排行榜失败。')
}

import type { RecordSummary, ScoreProgressUnit, ScoreStats, WrongQuestionRecord, SyncStatsIn } from '@/types/api'
import { requestJson } from './http'

const BASE = '/api'

export async function fetchRecordSummary(token: string): Promise<RecordSummary> {
  return requestJson<RecordSummary>(`${BASE}/records/summary`, {
    headers: { 'Authorization': `Bearer ${token}` }
  }, '加载学习汇总失败。')
}

export async function fetchScoreStats(token: string): Promise<ScoreStats> {
  return requestJson<ScoreStats>(`${BASE}/scores/stats`, {
    headers: { 'Authorization': `Bearer ${token}` }
  }, '加载学习统计失败。')
}

export async function fetchScoreProgress(token: string): Promise<ScoreProgressUnit[]> {
  return requestJson<ScoreProgressUnit[]>(`${BASE}/scores/progress`, {
    headers: { 'Authorization': `Bearer ${token}` }
  }, '加载关卡进度失败。')
}

export async function fetchWrongQuestionRecords(token: string, limit = 40): Promise<WrongQuestionRecord[]> {
  return requestJson<WrongQuestionRecord[]>(`${BASE}/records/wrong?limit=${limit}`, {
    headers: { 'Authorization': `Bearer ${token}` }
  }, '加载错题记录失败。')
}

export async function syncStats(body: SyncStatsIn, token: string): Promise<RecordSummary> {
  return requestJson<RecordSummary>(`${BASE}/records/stats`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  }, '同步统计失败。')
}

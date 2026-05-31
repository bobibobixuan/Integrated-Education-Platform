import type {
  StudentPvpRoomOut, PvpReadyUpdateIn,
  PvpBattleSession, PvpBattleAnswerIn, PvpBattleAnswerOut,
  PvpFinalizeIn, PvpRoom,
} from '@/types/api'
import { requestJson } from './http'

const BASE = '/api/pvp'
const getHeaders = (token: string) => ({
  'Authorization': `Bearer ${token}`,
  'Content-Type': 'application/json',
})

export async function getMyRoom(token: string): Promise<StudentPvpRoomOut> {
  return requestJson<StudentPvpRoomOut>(`${BASE}/my-room`, {
    headers: { 'Authorization': `Bearer ${token}` }
  }, '加载房间状态失败。')
}

export async function listRooms(token: string): Promise<PvpRoom[]> {
  return requestJson<PvpRoom[]>(`${BASE}/rooms`, {
    headers: { 'Authorization': `Bearer ${token}` }
  }, '加载房间列表失败。')
}

export interface StudentCreateRoomIn {
  title: string; description?: string; group_size: number
  question_unit_ids: number[]; question_count: number
  battle_time_limit_seconds?: number
}

export async function createRoom(body: StudentCreateRoomIn, token: string): Promise<PvpRoom> {
  return requestJson<PvpRoom>(`${BASE}/rooms`, {
    method: 'POST', headers: getHeaders(token), body: JSON.stringify(body)
  }, '创建房间失败。')
}

export async function joinRoom(roomId: number, token: string): Promise<StudentPvpRoomOut> {
  return requestJson<StudentPvpRoomOut>(`${BASE}/rooms/${roomId}/join`, {
    method: 'POST', headers: getHeaders(token)
  }, '加入房间失败。')
}

export async function updateReady(body: PvpReadyUpdateIn, token: string): Promise<StudentPvpRoomOut> {
  return requestJson<StudentPvpRoomOut>(`${BASE}/my-room/ready`, {
    method: 'PUT', headers: getHeaders(token), body: JSON.stringify(body)
  }, '更新准备状态失败。')
}

export async function leaveRoom(token: string): Promise<StudentPvpRoomOut> {
  return requestJson<StudentPvpRoomOut>(`${BASE}/my-room/leave`, {
    method: 'POST', headers: getHeaders(token)
  }, '退出房间失败。')
}

export async function getMyBattle(token: string): Promise<PvpBattleSession> {
  return requestJson<PvpBattleSession>(`${BASE}/my-battle`, {
    headers: { 'Authorization': `Bearer ${token}` }
  }, '加载对战状态失败。')
}

export async function submitPvpAnswer(body: PvpBattleAnswerIn, token: string): Promise<PvpBattleAnswerOut> {
  return requestJson<PvpBattleAnswerOut>(`${BASE}/answer`, {
    method: 'POST', headers: getHeaders(token), body: JSON.stringify(body)
  }, '提交对战答案失败。')
}

export async function finalizeSession(body: PvpFinalizeIn, token: string): Promise<PvpRoom> {
  return requestJson<PvpRoom>(`${BASE}/finalize-session`, {
    method: 'POST', headers: getHeaders(token), body: JSON.stringify(body)
  }, '结算对战结果失败。')
}

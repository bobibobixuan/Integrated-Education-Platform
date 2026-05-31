import type {
  AdminDashboardOut, AdminLevelAnalyticsItem, AdminPvpRoomCreate, AdminQuestionsResponse,
  AdminStudentDetail, AdminStudentsResponse, AdminUser, AdminWrongQuestionItem,
  PublicRegistrationSetting, PvpRoom, UnitOut,
} from '@/types/api'
import { requestJson } from './http'

const BASE = '/api/admin'
const getHeaders = (token: string) => ({
  'Authorization': `Bearer ${token}`,
  'Content-Type': 'application/json',
})

// ── Units (shared, used by both admin and student) ──

export async function getUnits(token: string): Promise<UnitOut[]> {
  return requestJson<UnitOut[]>('/api/units/', {
    headers: { 'Authorization': `Bearer ${token}` }
  }, '加载单元列表失败。')
}

// ── Users ──

export async function fetchUsers(token: string): Promise<AdminUser[]> {
  return requestJson<AdminUser[]>(`${BASE}/users`, {
    headers: { 'Authorization': `Bearer ${token}` }
  }, '加载用户列表失败。')
}

export async function fetchDashboard(token: string): Promise<AdminDashboardOut> {
  return requestJson<AdminDashboardOut>(`${BASE}/dashboard`, {
    headers: { 'Authorization': `Bearer ${token}` }
  }, '加载仪表盘失败。')
}

export async function fetchStudents(
  token: string, page = 1, pageSize = 20, search = '', sortBy = 'total_score', order = 'desc', includeDisabled = false
): Promise<AdminStudentsResponse> {
  const params = new URLSearchParams({
    page: String(page), page_size: String(pageSize),
    search, sort_by: sortBy, order, include_disabled: String(includeDisabled),
  })
  return requestJson<AdminStudentsResponse>(`${BASE}/students?${params}`, {
    headers: { 'Authorization': `Bearer ${token}` }
  }, '加载学生列表失败。')
}

export async function createStudent(
  token: string, body: { username: string; nickname: string; password: string }
): Promise<unknown> {
  return requestJson<unknown>(`${BASE}/students`, {
    method: 'POST', headers: getHeaders(token), body: JSON.stringify(body)
  }, '创建学生失败。')
}

export async function fetchStudentDetail(token: string, userId: number): Promise<AdminStudentDetail> {
  return requestJson<AdminStudentDetail>(`${BASE}/students/${userId}`, {
    headers: { 'Authorization': `Bearer ${token}` }
  }, '加载学生详情失败。')
}

export async function importStudents(
  token: string,
  body: { students: Array<{ username: string; nickname: string; password: string }> }
): Promise<{ message: string; created: number }> {
  return requestJson<{ message: string; created: number }>(`${BASE}/students/import`, {
    method: 'POST', headers: getHeaders(token), body: JSON.stringify(body)
  }, '批量导入学生失败。')
}

export async function updateStudent(
  token: string, userId: number, body: Record<string, unknown>
): Promise<unknown> {
  return requestJson<unknown>(`${BASE}/students/${userId}`, {
    method: 'PUT', headers: getHeaders(token), body: JSON.stringify(body)
  }, '更新学生失败。')
}

export async function disableStudent(token: string, userId: number): Promise<unknown> {
  return requestJson<unknown>(`${BASE}/students/${userId}`, {
    method: 'DELETE', headers: { 'Authorization': `Bearer ${token}` }
  }, '禁用学生失败。')
}

// ── Questions ──

export async function fetchQuestions(
  token: string, page = 1, pageSize = 20, levelId?: number, unitId?: number, type = '', search = '', includeInactive = false
): Promise<AdminQuestionsResponse> {
  const params = new URLSearchParams({
    page: String(page), page_size: String(pageSize), include_inactive: String(includeInactive),
  })
  if (levelId) params.set('level_id', String(levelId))
  if (unitId) params.set('unit_id', String(unitId))
  if (type) params.set('question_type', type)
  if (search) params.set('search', search)
  return requestJson<AdminQuestionsResponse>(`${BASE}/questions?${params}`, {
    headers: { 'Authorization': `Bearer ${token}` }
  }, '加载题目列表失败。')
}

export async function fetchLevelAnalytics(token: string): Promise<AdminLevelAnalyticsItem[]> {
  return requestJson<AdminLevelAnalyticsItem[]>(`${BASE}/analytics/levels`, {
    headers: { 'Authorization': `Bearer ${token}` }
  }, '加载关卡分析失败。')
}

export async function fetchWrongQuestionStats(token: string, limit = 50): Promise<AdminWrongQuestionItem[]> {
  return requestJson<AdminWrongQuestionItem[]>(`${BASE}/analytics/wrong-questions?limit=${limit}`, {
    headers: { 'Authorization': `Bearer ${token}` }
  }, '加载错题统计失败。')
}

export async function getRegistrationSetting(token: string): Promise<PublicRegistrationSetting> {
  return requestJson<PublicRegistrationSetting>(`${BASE}/settings/registration`, {
    headers: { 'Authorization': `Bearer ${token}` }
  }, '加载注册开关失败。')
}

export async function updateRegistrationSetting(token: string, allowSelfRegister: boolean): Promise<PublicRegistrationSetting> {
  return requestJson<PublicRegistrationSetting>(`${BASE}/settings/registration`, {
    method: 'PUT',
    headers: getHeaders(token),
    body: JSON.stringify({ allow_self_register: allowSelfRegister }),
  }, '更新注册开关失败。')
}

export async function importQuestions(token: string, body: Record<string, unknown>): Promise<{ message: string }> {
  return requestJson<{ message: string }>(`${BASE}/import`, {
    method: 'POST', headers: getHeaders(token), body: JSON.stringify(body)
  }, '题库导入失败。')
}

export async function importQuestionsExcel(token: string, file: File, unit: string): Promise<{ message: string }> {
  const formData = new FormData()
  formData.append('file', file)
  const params = new URLSearchParams({ unit })
  const res = await fetch(`${BASE}/import/excel?${params}`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
    body: formData,
  })
  if (!res.ok) {
    let detail = 'Excel 导入失败。'
    try {
      const body = await res.json() as { detail?: string }
      if (body.detail) detail = body.detail
    } catch { /* ignore */ }
    throw new Error(detail)
  }
  return res.json() as Promise<{ message: string }>
}

// ── PvP Rooms (admin) ──

export async function fetchPvpRooms(token: string): Promise<PvpRoom[]> {
  return requestJson<PvpRoom[]>(`${BASE}/pvp/rooms`, {
    headers: { 'Authorization': `Bearer ${token}` }
  }, '加载竞技房间失败。')
}

export async function createPvpRoom(token: string, body: AdminPvpRoomCreate): Promise<PvpRoom> {
  return requestJson<PvpRoom>(`${BASE}/pvp/rooms`, {
    method: 'POST', headers: getHeaders(token), body: JSON.stringify(body)
  }, '创建竞技房间失败。')
}

export async function updatePvpRoom(token: string, roomId: number, body: AdminPvpRoomCreate): Promise<PvpRoom> {
  return requestJson<PvpRoom>(`${BASE}/pvp/rooms/${roomId}`, {
    method: 'PUT', headers: getHeaders(token), body: JSON.stringify(body)
  }, '更新竞技房间失败。')
}

export async function startPvpRoom(token: string, roomId: number): Promise<PvpRoom> {
  return requestJson<PvpRoom>(`${BASE}/pvp/rooms/${roomId}/start`, {
    method: 'POST', headers: getHeaders(token)
  }, '开始竞技房间失败。')
}

export async function finishPvpRoom(token: string, roomId: number): Promise<PvpRoom> {
  return requestJson<PvpRoom>(`${BASE}/pvp/rooms/${roomId}/finish`, {
    method: 'POST', headers: getHeaders(token)
  }, '结束竞技房间失败。')
}

// ── Question CRUD ──

export async function createQuestion(
  token: string, body: import('@/types/api').QuestionCreatePayload
): Promise<{ id: number; message: string }> {
  return requestJson(`${BASE}/questions`, {
    method: 'POST', headers: getHeaders(token), body: JSON.stringify(body)
  }, '创建题目失败。')
}

export async function updateQuestion(
  token: string, questionId: number, body: import('@/types/api').QuestionUpdatePayload
): Promise<{ id: number; message: string }> {
  return requestJson(`${BASE}/questions/${questionId}`, {
    method: 'PUT', headers: getHeaders(token), body: JSON.stringify(body)
  }, '更新题目失败。')
}

export async function toggleQuestion(
  token: string, questionId: number, isActive: boolean
): Promise<{ id: number; message: string }> {
  return requestJson(`${BASE}/questions/${questionId}`, {
    method: isActive ? 'PUT' : 'DELETE',
    headers: getHeaders(token),
    body: isActive ? JSON.stringify({ is_active: true }) : undefined,
  }, isActive ? '启用题目失败。' : '禁用题目失败。')
}

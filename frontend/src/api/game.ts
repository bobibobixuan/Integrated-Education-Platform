import type {
  UnitOut, LevelOut,
  StartSessionIn, StartSessionOut,
  NextQuestionIn, NextQuestionOut,
  AnswerSubmit, AnswerSubmitResponse,
  QuestionOut,
} from '@/types/api'
import { requestJson } from './http'

const BASE = '/api'
const getHeaders = (token: string) => ({
  'Authorization': `Bearer ${token}`,
  'Content-Type': 'application/json',
})

// ── Practice / fetch all questions for a unit ──

export async function fetchUnitQuestions(unitId: number, token: string): Promise<QuestionOut[]> {
  return requestJson<QuestionOut[]>(`${BASE}/questions/units/${unitId}`, {
    headers: { 'Authorization': `Bearer ${token}` }
  }, '加载题目失败。')
}

// ── Units ──

export async function fetchUnits(token: string): Promise<UnitOut[]> {
  return requestJson<UnitOut[]>(`${BASE}/units/with-levels`, {
    headers: { 'Authorization': `Bearer ${token}` }
  }, '加载单元列表失败。')
}

export async function fetchLevels(unitId: number, token: string): Promise<LevelOut[]> {
  return requestJson<LevelOut[]>(`${BASE}/units/${unitId}/levels`, {
    headers: { 'Authorization': `Bearer ${token}` }
  }, '加载关卡列表失败。')
}

// ── Session ──

export async function startSession(body: StartSessionIn, token: string): Promise<StartSessionOut> {
  return requestJson<StartSessionOut>(`${BASE}/records/start-session`, {
    method: 'POST', headers: getHeaders(token), body: JSON.stringify({ ...body, mode: body.mode || 'adventure' })
  }, '开始关卡失败。')
}

export async function nextQuestion(body: NextQuestionIn, token: string): Promise<NextQuestionOut> {
  return requestJson<NextQuestionOut>(`${BASE}/records/next-question`, {
    method: 'POST', headers: getHeaders(token), body: JSON.stringify(body)
  }, '加载下一题失败。')
}

export async function submitAnswer(body: AnswerSubmit, token: string): Promise<AnswerSubmitResponse> {
  return requestJson<AnswerSubmitResponse>(`${BASE}/records/answer`, {
    method: 'POST', headers: getHeaders(token), body: JSON.stringify(body)
  }, '提交答案失败。')
}

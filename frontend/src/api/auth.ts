import type {
  LoginRequest,
  RegisterRequest,
  TokenResponse,
  UserResponse,
  PasswordChangeRequest,
  ProfileUpdateRequest,
} from '@/types/api'
import { requestJson } from './http'

const BASE = '/api/auth'

export async function login(data: LoginRequest): Promise<TokenResponse> {
  return requestJson<TokenResponse>(`${BASE}/login`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data)
  }, '登录失败，请检查账号或密码。')
}

export async function register(data: RegisterRequest): Promise<TokenResponse> {
  return requestJson<TokenResponse>(`${BASE}/register`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data)
  }, '注册失败，请稍后重试。')
}

export async function getMe(token: string): Promise<UserResponse> {
  return requestJson<UserResponse>(`${BASE}/me`, {
    headers: { 'Authorization': `Bearer ${token}` }
  }, '读取当前用户信息失败。')
}

export async function changePassword(token: string, data: PasswordChangeRequest): Promise<TokenResponse> {
  return requestJson<TokenResponse>(`${BASE}/password`, {
    method: 'PUT', headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` }, body: JSON.stringify(data)
  }, '修改密码失败。')
}

export async function updateProfile(token: string, data: ProfileUpdateRequest): Promise<UserResponse> {
  return requestJson<UserResponse>(`${BASE}/profile`, {
    method: 'PUT', headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` }, body: JSON.stringify(data)
  }, '更新个人资料失败。')
}

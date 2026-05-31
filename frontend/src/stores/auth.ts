import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as apiLogin, register as apiRegister, getMe, changePassword as apiChangePassword, updateProfile as apiUpdateProfile } from '@/api/auth'
import { useWebSocketStore } from './websocket'
import type { UserResponse } from '@/types/api'

const TOKEN_KEY = 'token'
const USER_KEY = 'auth_user'

function readStoredUser(): UserResponse | null {
  const raw = localStorage.getItem(USER_KEY)
  if (!raw) return null

  try {
    return JSON.parse(raw) as UserResponse
  } catch {
    localStorage.removeItem(USER_KEY)
    return null
  }
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem(TOKEN_KEY))
  const user = ref<UserResponse | null>(readStoredUser())
  const restoring = ref(false)
  const isAuthenticated = computed(() => !!token.value && !!user.value)

  function persistSession(nextToken: string, nextUser: UserResponse) {
    const wsStore = useWebSocketStore()
    token.value = nextToken
    user.value = nextUser
    localStorage.setItem(TOKEN_KEY, nextToken)
    localStorage.setItem(USER_KEY, JSON.stringify(nextUser))
    wsStore.syncAuth()
  }

  async function restoreSession() {
    if (!token.value || restoring.value) return

    restoring.value = true
    try {
      const me = await getMe(token.value)
      user.value = me
      localStorage.setItem(USER_KEY, JSON.stringify(me))
      useWebSocketStore().syncAuth()
    } catch {
      logout()
    } finally {
      restoring.value = false
    }
  }

  async function doLogin(username: string, password: string) {
    const res = await apiLogin({ username, password })
    const me = await getMe(res.access_token)
    persistSession(res.access_token, me)
  }

  async function doRegister(username: string, password: string, nickname: string) {
    const res = await apiRegister({ username, password, nickname })
    const me = await getMe(res.access_token)
    persistSession(res.access_token, me)
  }

  async function updateNickname(nickname: string) {
    if (!token.value) throw new Error('当前未登录。')
    const updated = await apiUpdateProfile(token.value, { nickname })
    user.value = updated
    localStorage.setItem(USER_KEY, JSON.stringify(updated))
  }

  async function updatePassword(oldPassword: string, newPassword: string) {
    if (!token.value) throw new Error('当前未登录。')
    const res = await apiChangePassword(token.value, {
      old_password: oldPassword,
      new_password: newPassword,
    })
    const me = await getMe(res.access_token)
    persistSession(res.access_token, me)
  }

  function logout() {
    const wsStore = useWebSocketStore()
    token.value = null
    user.value = null
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
    wsStore.disconnect()
  }

  return {
    token,
    user,
    restoring,
    isAuthenticated,
    restoreSession,
    doLogin,
    doRegister,
    updateNickname,
    updatePassword,
    logout,
  }
})

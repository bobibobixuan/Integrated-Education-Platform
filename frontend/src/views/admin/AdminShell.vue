<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  DataAnalysis,
  Fold,
  House,
  Notebook,
  Reading,
  SwitchButton,
  Trophy,
  UserFilled,
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getMe, login } from '@/api/auth'
import { ADMIN_ENGLISH_NAME, ADMIN_NAME } from '@/brand'
import type { UserResponse } from '@/types/api'
import './admin-theme.css'

const ADMIN_TOKEN_KEY = 'admin_token'
const LEGACY_ADMIN_TOKEN_KEY = 'admin_jwt_token'
const ADMIN_USER_KEY = 'admin_user'

const route = useRoute()
const router = useRouter()

const restoring = ref(false)
const loading = ref(false)
const collapsed = ref(false)
const isNarrow = ref(false)
const adminToken = ref<string | null>(null)
const adminUser = ref<UserResponse | null>(null)
const loginForm = ref({ username: '', password: '' })

const menuItems = [
  { path: '/admin/dashboard', label: '仪表盘', icon: House },
  { path: '/admin/students', label: '学生管理', icon: UserFilled },
  { path: '/admin/questions', label: '题库管理', icon: Notebook },
  { path: '/admin/analytics', label: '教学分析', icon: DataAnalysis },
  { path: '/admin/pvp', label: 'PVP 管理', icon: Trophy },
]

const hasAdminSession = computed(() => Boolean(adminToken.value && adminUser.value))
const adminDisplayName = computed(() => adminUser.value?.nickname || adminUser.value?.username || '管理员')
const activeMenu = computed(() => route.path)
const shellAsideWidth = computed(() => (collapsed.value ? '72px' : '232px'))

function readStoredAdminUser(): UserResponse | null {
  const raw = localStorage.getItem(ADMIN_USER_KEY)
  if (!raw) return null
  try {
    return JSON.parse(raw) as UserResponse
  } catch {
    localStorage.removeItem(ADMIN_USER_KEY)
    return null
  }
}

function readStoredAdminSession() {
  const token = localStorage.getItem(ADMIN_TOKEN_KEY) || localStorage.getItem(LEGACY_ADMIN_TOKEN_KEY)
  const user = readStoredAdminUser()

  if (token && localStorage.getItem(ADMIN_TOKEN_KEY) !== token) {
    localStorage.setItem(ADMIN_TOKEN_KEY, token)
  }

  if (!token && user) {
    localStorage.removeItem(ADMIN_USER_KEY)
    return { token: null, user: null }
  }

  return { token, user }
}

function persistAdminSession(token: string, user: UserResponse) {
  adminToken.value = token
  adminUser.value = user
  localStorage.setItem(ADMIN_TOKEN_KEY, token)
  localStorage.removeItem(LEGACY_ADMIN_TOKEN_KEY)
  localStorage.setItem(ADMIN_USER_KEY, JSON.stringify(user))
}

function clearAdminSession() {
  adminToken.value = null
  adminUser.value = null
  localStorage.removeItem(ADMIN_TOKEN_KEY)
  localStorage.removeItem(LEGACY_ADMIN_TOKEN_KEY)
  localStorage.removeItem(ADMIN_USER_KEY)
}

function getErrorMessage(error: unknown) {
  return error instanceof Error ? error.message : '操作失败，请稍后重试。'
}

function syncViewportState() {
  isNarrow.value = window.innerWidth < 900
  collapsed.value = isNarrow.value
}

async function restoreAdminSession() {
  const stored = readStoredAdminSession()
  adminToken.value = stored.token
  adminUser.value = stored.user
  if (!stored.token) return

  restoring.value = true
  try {
    const me = await getMe(stored.token)
    if (me.role !== 'admin') {
      clearAdminSession()
      return
    }
    persistAdminSession(stored.token, me)
  } catch {
    clearAdminSession()
  } finally {
    restoring.value = false
  }
}

async function handleAdminLogin() {
  loading.value = true
  try {
    const tokenRes = await login(loginForm.value)
    const me = await getMe(tokenRes.access_token)
    if (me.role !== 'admin') {
      throw new Error('该账号不是管理员。')
    }
    persistAdminSession(tokenRes.access_token, me)
    loginForm.value.password = ''
    ElMessage.success('登录成功，已进入教师管理后台。')
  } catch (error) {
    ElMessage.error(getErrorMessage(error))
  } finally {
    loading.value = false
  }
}

function handleAdminLogout() {
  clearAdminSession()
  ElMessage.success('已退出教师管理后台。')
  void router.replace('/admin/dashboard')
}

onMounted(() => {
  syncViewportState()
  window.addEventListener('resize', syncViewportState)
  void restoreAdminSession()
})

onUnmounted(() => {
  window.removeEventListener('resize', syncViewportState)
})
</script>

<template>
  <div class="admin-shell" data-theme="admin">
    <div v-if="!hasAdminSession" class="admin-login-page">
      <el-card class="admin-login-card" shadow="never">
        <div class="admin-login-card__brand">
          <el-icon :size="34"><Reading /></el-icon>
          <div>
            <span>{{ ADMIN_ENGLISH_NAME }}</span>
            <h1>{{ ADMIN_NAME }}</h1>
          </div>
        </div>

        <el-alert
          v-if="restoring"
          title="正在恢复管理员会话..."
          type="info"
          :closable="false"
          show-icon
        />

        <el-form class="admin-login-form" :model="loginForm" label-position="top" @submit.prevent="handleAdminLogin">
          <el-form-item label="管理员账号">
            <el-input v-model.trim="loginForm.username" autocomplete="username" />
          </el-form-item>
          <el-form-item label="密码">
            <el-input v-model="loginForm.password" type="password" autocomplete="current-password" show-password />
          </el-form-item>
          <el-button type="primary" native-type="submit" :loading="loading" class="admin-login-form__submit">
            登录后台
          </el-button>
        </el-form>
      </el-card>
    </div>

    <el-container v-else class="admin-shell__layout">
      <el-aside :width="shellAsideWidth" class="admin-shell__aside">
        <div class="admin-shell__brand" :class="{ 'admin-shell__brand--collapsed': collapsed }">
          <el-icon :size="26"><Reading /></el-icon>
          <div v-if="!collapsed">
            <strong>{{ ADMIN_NAME }}</strong>
            <span>{{ ADMIN_ENGLISH_NAME }}</span>
          </div>
        </div>

        <el-menu
          router
          :default-active="activeMenu"
          :collapse="collapsed"
          class="admin-shell__menu"
          background-color="#101827"
          text-color="#cbd5e1"
          active-text-color="#ffffff"
        >
          <el-menu-item v-for="item in menuItems" :key="item.path" :index="item.path">
            <el-icon><component :is="item.icon" /></el-icon>
            <template #title>{{ item.label }}</template>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <el-container>
        <el-header class="admin-shell__header">
          <div class="admin-shell__header-left">
            <el-button text :icon="Fold" @click="collapsed = !collapsed" />
            <span>后台工作台</span>
          </div>
          <div class="admin-shell__header-right">
            <el-tag v-if="adminUser?.force_password_change" type="warning">需要修改初始密码</el-tag>
            <span class="admin-shell__user">{{ adminDisplayName }}</span>
            <el-button :icon="SwitchButton" @click="handleAdminLogout">退出</el-button>
          </div>
        </el-header>

        <el-main class="admin-shell__main">
          <RouterView />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<style scoped>
.admin-shell {
  height: 100dvh;
  min-height: 100vh;
  overflow: hidden;
  background: var(--admin-bg);
  color: var(--admin-text);
  font-family: var(--font-body);
}

.admin-login-page {
  display: grid;
  min-height: 100vh;
  place-items: center;
  padding: 24px;
  background: var(--admin-bg);
}

.admin-login-card {
  width: min(420px, 100%);
  border: 1px solid var(--admin-border);
  border-radius: 20px;
  box-shadow: var(--admin-shadow);
}

.admin-login-card__brand {
  display: flex;
  gap: 14px;
  align-items: center;
  margin-bottom: 22px;
  color: var(--admin-text);
}

.admin-login-card__brand span {
  display: block;
  color: var(--admin-muted);
  font-size: 13px;
}

.admin-login-card__brand h1 {
  margin: 4px 0 0;
  font-size: 24px;
  line-height: 1.2;
}

.admin-login-form {
  margin-top: 16px;
}

.admin-login-form__submit {
  width: 100%;
}

.admin-shell__layout {
  height: 100%;
  min-height: 0;
}

.admin-shell__layout :deep(.el-container) {
  min-width: 0;
  min-height: 0;
  overflow: hidden;
}

.admin-shell__aside {
  flex-shrink: 0;
  height: 100%;
  overflow: hidden;
  background: #101827;
  box-shadow: 8px 0 28px rgba(15, 23, 42, 0.12);
  transition: width 180ms ease;
}

.admin-shell__brand {
  display: flex;
  gap: 12px;
  align-items: center;
  min-height: 72px;
  padding: 0 18px;
  color: #ffffff;
}

.admin-shell__brand--collapsed {
  justify-content: center;
  padding: 0;
}

.admin-shell__brand strong,
.admin-shell__brand span {
  display: block;
}

.admin-shell__brand strong {
  font-size: 16px;
}

.admin-shell__brand span {
  margin-top: 2px;
  color: var(--admin-faint);
  font-size: 12px;
}

.admin-shell__menu {
  height: calc(100% - 72px);
  overflow-y: auto;
  border-right: 0;
  padding: 8px;
  background: transparent;
  scrollbar-gutter: stable;
}

.admin-shell__menu :deep(.el-menu-item) {
  height: 44px;
  margin-bottom: 6px;
  border-radius: 12px;
}

.admin-shell__menu :deep(.el-menu-item.is-active) {
  background: rgba(37, 99, 235, 0.22);
}

.admin-shell__menu :deep(.el-menu-item:not(.is-active):hover) {
  background: rgba(255, 255, 255, 0.07);
}

.admin-shell__header {
  display: flex;
  flex-shrink: 0;
  align-items: center;
  justify-content: space-between;
  height: 68px;
  border-bottom: 1px solid var(--admin-border);
  background: rgba(255, 255, 255, 0.92);
}

.admin-shell__header-left,
.admin-shell__header-right {
  display: flex;
  gap: 12px;
  align-items: center;
}

.admin-shell__header-left span {
  font-weight: 700;
}

.admin-shell__user {
  color: #334155;
  font-size: 14px;
}

.admin-shell__main {
  height: calc(100dvh - 68px);
  min-height: 0;
  overflow: auto;
  padding: 24px;
  background: var(--admin-bg);
  scrollbar-gutter: stable;
}

@media (max-width: 720px) {
  .admin-shell__header {
    gap: 12px;
    height: auto;
    min-height: 60px;
    padding: 10px 12px;
  }

  .admin-shell__header-right {
    gap: 8px;
  }

  .admin-shell__user {
    display: none;
  }

  .admin-shell__main {
    height: calc(100dvh - 60px);
    padding: 14px;
  }
}
</style>

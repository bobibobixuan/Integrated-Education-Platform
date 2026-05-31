<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import BrandLogo from '@/components/BrandLogo.vue'
import { APP_NAME } from '@/brand'
import { normalizeRedirectTarget } from '@/lib/student-navigation'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const isRegister = ref(false)
const username = ref('')
const password = ref('')
const nickname = ref('')
const errorMsg = ref('')
const loading = ref(false)

const submitLabel = computed(() => (isRegister.value ? '创建账号' : '登录'))

async function handleSubmit() {
  errorMsg.value = ''

  if (!username.value.trim() || !password.value.trim()) {
    errorMsg.value = '请填写用户名和密码。'
    return
  }

  if (isRegister.value && !nickname.value.trim()) {
    errorMsg.value = '请填写昵称。'
    return
  }

  loading.value = true
  try {
    if (isRegister.value) {
      await auth.doRegister(username.value.trim(), password.value, nickname.value.trim())
    } else {
      await auth.doLogin(username.value.trim(), password.value)
    }

    if (auth.user?.role === 'admin') {
      auth.logout()
      errorMsg.value = '管理员请使用管理端入口登录。'
      return
    }

    router.push(normalizeRedirectTarget(route.query.redirect, '/'))
  } catch (error) {
    errorMsg.value = error instanceof Error ? error.message : '操作失败。'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <!-- Brand -->
    <header class="login-brand">
      <BrandLogo size="lg" :alt="APP_NAME" />
      <h1 class="login-title">{{ APP_NAME }}</h1>
      <p class="login-subtitle">登录后继续学习、闯关和 PVP 对战</p>
    </header>

    <!-- Login Card -->
    <section class="login-card">
      <!-- Segmented Control -->
      <div class="login-tabs">
        <button type="button" class="login-tab" :class="{ active: !isRegister }" @click="isRegister = false">登录</button>
        <button type="button" class="login-tab" :class="{ active: isRegister }" @click="isRegister = true">注册</button>
      </div>

      <!-- Error Banner -->
      <div v-if="errorMsg" class="login-error">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
        <span>{{ errorMsg }}</span>
        <button type="button" class="login-error-close" @click="errorMsg = ''">✕</button>
      </div>

      <!-- Form -->
      <form class="login-form" @submit.prevent="handleSubmit">
        <input v-model="username" type="text" placeholder="用户名" autocomplete="username" class="login-input" />
        <input v-model="password" type="password" placeholder="密码" :autocomplete="isRegister ? 'new-password' : 'current-password'" class="login-input" />
        <input v-if="isRegister" v-model="nickname" type="text" placeholder="昵称" autocomplete="nickname" class="login-input" />

        <button type="submit" class="login-submit" :disabled="loading">
          {{ loading ? '处理中…' : submitLabel }}
        </button>
      </form>
    </section>

    <!-- Bottom Links -->
    <div class="login-links">
      <button type="button" class="login-link-back" @click="router.push('/')">← 返回首页</button>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  background: #F2F2F7;
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "PingFang SC", "Microsoft YaHei", sans-serif;
  gap: 28px;
}

/* ── Brand ── */
.login-brand {
  text-align: center;
}

.login-title {
  margin: 14px 0 6px;
  font-size: 34px;
  font-weight: 700;
  color: #000000;
  letter-spacing: -0.02em;
}

.login-subtitle {
  margin: 0;
  font-size: 16px;
  color: rgba(60, 60, 67, 0.6);
}

/* ── Card ── */
.login-card {
  width: 520px;
  max-width: 100%;
  background: #FFFFFF;
  border-radius: 20px;
  border: 1px solid rgba(60, 60, 67, 0.12);
  box-shadow: 0 18px 45px rgba(0, 0, 0, 0.08);
  padding: 32px;
}

/* ── Segmented Control ── */
.login-tabs {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0;
  padding: 4px;
  background: #F2F2F7;
  border-radius: 12px;
  margin-bottom: 20px;
}

.login-tab {
  height: 44px;
  border: none;
  border-radius: 10px;
  background: transparent;
  color: rgba(60, 60, 67, 0.6);
  font-size: 15px;
  font-weight: 500;
  font-family: inherit;
  cursor: pointer;
  transition: background 0.15s, color 0.15s, box-shadow 0.15s;
}

.login-tab.active {
  background: #FFFFFF;
  color: #007AFF;
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

/* ── Error Banner ── */
.login-error {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  margin-bottom: 18px;
  border-radius: 12px;
  background: rgba(255, 59, 48, 0.08);
  border: 1px solid rgba(255, 59, 48, 0.35);
  color: #FF3B30;
  font-size: 14px;
}

.login-error span {
  flex: 1;
}

.login-error-close {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 6px;
  background: rgba(255, 59, 48, 0.12);
  color: #FF3B30;
  font-size: 12px;
  cursor: pointer;
}

/* ── Form ── */
.login-form {
  display: grid;
  gap: 14px;
}

.login-input {
  height: 46px;
  padding: 0 14px;
  border-radius: 12px;
  border: 1px solid rgba(60, 60, 67, 0.18);
  background: #FFFFFF;
  font-size: 15px;
  color: #000000;
  font-family: inherit;
  outline: none;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.login-input::placeholder {
  color: rgba(60, 60, 67, 0.35);
}

.login-input:focus {
  border-color: #007AFF;
  box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.12);
}

/* ── Submit Button ── */
.login-submit {
  width: 100%;
  height: 48px;
  border: none;
  border-radius: 12px;
  background: #007AFF;
  color: #FFFFFF;
  font-size: 16px;
  font-weight: 600;
  font-family: inherit;
  cursor: pointer;
  transition: background 0.15s, transform 0.1s, opacity 0.15s;
  margin-top: 4px;
}

.login-submit:hover:not(:disabled) {
  background: #006EE6;
}

.login-submit:active:not(:disabled) {
  transform: scale(0.98);
}

.login-submit:disabled {
  background: rgba(0, 122, 255, 0.35);
  cursor: not-allowed;
}

/* ── Bottom Links ── */
.login-links {
  display: flex;
  align-items: center;
  gap: 24px;
}

.login-link-back {
  border: none;
  background: none;
  color: rgba(60, 60, 67, 0.6);
  font-size: 15px;
  font-family: inherit;
  cursor: pointer;
  padding: 8px 12px;
  border-radius: 8px;
  transition: color 0.15s, background 0.15s;
}

.login-link-back:hover {
  color: #007AFF;
  background: rgba(0, 122, 255, 0.04);
}

/* ── Responsive ── */
@media (max-width: 640px) {
  .login-page {
    padding: 24px 16px;
  }

  .login-title {
    font-size: 28px;
  }

  .login-card {
    padding: 24px;
  }
}
</style>

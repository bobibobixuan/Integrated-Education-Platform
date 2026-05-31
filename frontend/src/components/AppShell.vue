<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import BrandLogo from '@/components/BrandLogo.vue'
import { APP_ENGLISH_NAME, APP_NAME } from '@/brand'

const props = withDefaults(defineProps<{
  title?: string
  backTo?: string
  compact?: boolean
}>(), {
  compact: false,
})

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const userLabel = computed(() => auth.user?.nickname || auth.user?.username || '未登录')
const shellTitle = computed(() => props.title || route.meta.title || APP_NAME)
const backTarget = computed(() => props.backTo || route.meta.backTo)

function goBack() {
  if (typeof backTarget.value === 'string' && backTarget.value) {
    router.push(backTarget.value)
    return
  }
  router.back()
}

function goHome() {
  router.push('/')
}

function goLogin() {
  router.push('/login')
}

function goAccount() {
  if (!auth.isAuthenticated) {
    goLogin()
    return
  }
  router.push('/account')
}

function handleLogout() {
  auth.logout()
  router.push('/')
}
</script>

<template>
  <div class="app-shell">
    <header class="app-shell__bar" :class="{ 'app-shell__bar--compact': props.compact }">
      <div class="app-shell__left">
        <button type="button" class="app-shell__ghost" @click="goBack" title="返回">
          ← 返回
        </button>
        <div class="app-shell__brand">
          <BrandLogo size="md" :alt="APP_NAME" />
          <div>
            <p class="app-shell__eyebrow">{{ APP_ENGLISH_NAME }}</p>
            <h1 class="app-shell__title">{{ shellTitle }}</h1>
          </div>
        </div>
      </div>

      <div class="app-shell__right">
        <div v-if="auth.isAuthenticated" class="app-shell__user">
          <span class="app-shell__user-label">当前账号</span>
          <strong>{{ userLabel }}</strong>
        </div>
        <button type="button" class="app-shell__ghost" @click="goAccount">
          {{ auth.isAuthenticated ? '个人中心' : '登录 / 注册' }}
        </button>

        <button type="button" class="app-shell__ghost" @click="goHome" title="首页">
          首页
        </button>
        <button
          v-if="auth.isAuthenticated"
          type="button"
          class="app-shell__danger"
          @click="handleLogout"
          title="退出登录"
        >
          退出
        </button>
      </div>
    </header>

    <main class="app-shell__main">
      <slot />
    </main>
  </div>
</template>

<style scoped>
.app-shell {
  min-height: 100vh;
  background: transparent;
}

.app-shell__bar {
  position: sticky;
  top: 12px;
  z-index: 100;
  width: min(1240px, calc(100% - 28px));
  margin: 12px auto 0;
  min-height: 82px;
  padding: 16px 18px 16px 22px;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 16px 18px;
  border: 1px solid var(--border);
  border-radius: 26px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.86), rgba(248, 248, 255, 0.7)),
    var(--bg-elevated);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  box-shadow: 0 18px 44px rgba(61, 72, 122, 0.12);
}

.app-shell__bar--compact {
  min-height: 72px;
}

.app-shell__left,
.app-shell__right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.app-shell__left {
  min-width: 0;
}

.app-shell__right {
  flex-wrap: wrap;
  justify-content: flex-end;
}

.app-shell__brand {
  display: flex;
  align-items: center;
  gap: 14px;
  min-width: 0;
}

.app-shell__eyebrow {
  margin: 0 0 3px;
  color: var(--text-tertiary);
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.app-shell__title {
  margin: 0;
  color: var(--text-primary);
  font-family: var(--font-display);
  font-size: 1.18rem;
  font-weight: 900;
  letter-spacing: -0.03em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.app-shell__user {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  min-width: 0;
  padding: 9px 12px;
  border-radius: 16px;
  border: 1px solid var(--border);
  background: rgba(255, 255, 255, 0.7);
}

.app-shell__user strong {
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--text-primary);
  font-size: 0.92rem;
}

.app-shell__user-label {
  color: var(--text-tertiary);
  font-size: 0.68rem;
  font-weight: 800;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.app-shell__ghost,
.app-shell__danger {
  min-height: 40px;
  padding: 0 15px;
  border-radius: 14px;
  border: 1px solid var(--border);
  background: rgba(255, 255, 255, 0.84);
  color: var(--text-secondary);
  font-size: 0.82rem;
  font-weight: 800;
  cursor: pointer;
  transition:
    transform var(--motion-fast) var(--ease-out),
    border-color var(--motion-fast) var(--ease-out),
    color var(--motion-fast) var(--ease-out),
    box-shadow var(--motion-fast) var(--ease-out);
}

.app-shell__ghost:hover,
.app-shell__danger:hover {
  transform: translateY(-2px);
  border-color: var(--border-strong);
  box-shadow: var(--shadow-sm);
}

.app-shell__ghost:hover {
  color: var(--text-primary);
}

.app-shell__danger {
  color: var(--danger);
  background: rgba(255, 240, 243, 0.9);
  border-color: rgba(212, 95, 120, 0.22);
}

.app-shell__main {
  width: min(1240px, calc(100% - 32px));
  margin: 0 auto;
  padding: 28px 0 78px;
  position: relative;
  z-index: 1;
}

@media (max-width: 980px) {
  .app-shell__bar {
    grid-template-columns: 1fr;
    padding: 14px;
  }

  .app-shell__left,
  .app-shell__right {
    width: 100%;
    justify-content: space-between;
  }

  .app-shell__right {
    justify-content: flex-start;
  }
}

@media (max-width: 640px) {
  .app-shell__main {
    width: calc(100% - 20px);
    padding-top: 20px;
  }

  .app-shell__left,
  .app-shell__right {
    flex-wrap: wrap;
    justify-content: flex-start;
  }

  .app-shell__brand {
    width: 100%;
  }

  .app-shell__title {
    font-size: 1rem;
  }

  .app-shell__user {
    width: 100%;
  }
}
</style>

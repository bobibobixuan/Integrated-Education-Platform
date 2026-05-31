<script setup lang="ts">
import { ref } from 'vue'
import BrandLogo from '@/components/BrandLogo.vue'
import { ADMIN_ENGLISH_NAME, ADMIN_NAME } from '@/brand'

const props = defineProps<{
  title: string
  userName: string
  activeTab: string
  tabs: Array<{ key: string; label: string }>
}>()

const emit = defineEmits<{
  (e: 'select', key: string): void
  (e: 'logout'): void
}>()

const collapsed = ref(false)
const mobileOpen = ref(false)

function handleSelect(key: string) {
  emit('select', key)
  mobileOpen.value = false
}
</script>

<template>
  <div
    class="admin-shell"
    :class="{
      'is-collapsed': collapsed,
      'is-mobile-open': mobileOpen,
    }"
    data-theme="admin"
  >
    <a class="admin-shell__skip" href="#admin-main">跳到主要内容</a>

    <div v-if="mobileOpen" class="admin-shell__backdrop" @click="mobileOpen = false" />

    <aside class="admin-shell__sidebar">
      <div class="admin-shell__brand">
        <BrandLogo size="md" :alt="ADMIN_NAME" />
        <div class="admin-shell__brand-copy">
          <strong>{{ ADMIN_NAME }}</strong>
          <span>{{ ADMIN_ENGLISH_NAME }}</span>
        </div>
        <button
          type="button"
          class="admin-shell__collapse"
          :aria-label="collapsed ? '展开侧栏' : '收起侧栏'"
          @click="collapsed = !collapsed"
        >
          <svg viewBox="0 0 20 20" aria-hidden="true">
            <path d="M12.5 4.5 7 10l5.5 5.5" />
          </svg>
        </button>
      </div>

      <nav class="admin-shell__nav" aria-label="教师端主导航">
        <button
          v-for="item in props.tabs"
          :key="item.key"
          type="button"
          class="admin-shell__nav-item"
          :class="{ 'is-active': props.activeTab === item.key }"
          :aria-current="props.activeTab === item.key ? 'page' : undefined"
          @click="handleSelect(item.key)"
        >
          <span class="admin-shell__nav-accent" aria-hidden="true" />
          <span class="admin-shell__nav-label">{{ item.label }}</span>
        </button>
      </nav>

      <div class="admin-shell__footer">
        <div class="admin-shell__user">
          <span>当前管理员</span>
          <strong>{{ props.userName }}</strong>
        </div>
        <div class="admin-shell__footer-actions">
          <button
            type="button"
            class="ghost-button admin-shell__footer-btn"
            aria-label="收起或展开侧栏"
            @click="collapsed = !collapsed"
          >
            {{ collapsed ? '展开侧栏' : '收起侧栏' }}
          </button>
          <button type="button" class="ghost-button admin-shell__footer-btn" @click="emit('logout')">退出登录</button>
        </div>
      </div>
    </aside>

    <main id="admin-main" class="admin-shell__main">
      <header class="admin-shell__header surface-card surface-card--strong">
        <div class="admin-shell__header-main">
          <button
            type="button"
            class="admin-shell__menu-trigger"
            aria-label="打开导航菜单"
            @click="mobileOpen = true"
          >
            <svg viewBox="0 0 20 20" aria-hidden="true">
              <path d="M3 5h14M3 10h14M3 15h14" />
            </svg>
          </button>
          <div>
            <span class="admin-shell__eyebrow">{{ ADMIN_ENGLISH_NAME }}</span>
            <h1>{{ props.title }}</h1>
          </div>
        </div>
        <div class="admin-shell__toolbar">
          <slot name="toolbar" />
        </div>
      </header>

      <section class="admin-shell__content">
        <slot />
      </section>
    </main>
  </div>
</template>

<style scoped>
.admin-shell {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr);
  background:
    radial-gradient(circle at 0 0, rgba(30, 64, 175, 0.08), transparent 18%),
    linear-gradient(180deg, #f8fafc 0%, #edf3f7 100%);
}

.admin-shell__skip {
  position: absolute;
  left: 16px;
  top: 16px;
  z-index: 90;
  padding: 10px 14px;
  border-radius: 999px;
  background: #1e40af;
  color: #ffffff;
  text-decoration: none;
  transform: translateY(-120%);
  transition: transform 180ms ease;
}

.admin-shell__skip:focus {
  transform: translateY(0);
}

.admin-shell__backdrop {
  position: fixed;
  inset: 0;
  z-index: 39;
  background: rgba(15, 23, 42, 0.42);
}

.admin-shell__sidebar {
  position: sticky;
  top: 0;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background:
    linear-gradient(180deg, rgba(15, 23, 42, 0.98), rgba(30, 41, 59, 0.98)),
    #0f172a;
  color: #e2e8f0;
  border-right: 1px solid rgba(148, 163, 184, 0.12);
  z-index: 40;
}

.admin-shell__brand {
  display: grid;
  grid-template-columns: 46px minmax(0, 1fr) 36px;
  align-items: center;
  gap: 14px;
  padding: 24px 20px 18px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.12);
}

.admin-shell__brand-copy {
  min-width: 0;
}

.admin-shell__brand-copy strong,
.admin-shell__user strong {
  display: block;
  color: #ffffff;
  font-size: 15px;
  font-weight: 700;
}

.admin-shell__brand-copy span,
.admin-shell__user span,
.admin-shell__eyebrow {
  display: block;
  color: #94a3b8;
  font-size: 11px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.admin-shell__collapse,
.admin-shell__menu-trigger {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  border: 1px solid rgba(148, 163, 184, 0.16);
  background: rgba(255, 255, 255, 0.04);
  color: #e2e8f0;
}

.admin-shell__collapse svg,
.admin-shell__menu-trigger svg {
  width: 18px;
  height: 18px;
  stroke: currentColor;
  stroke-width: 2;
  fill: none;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.admin-shell__nav {
  display: grid;
  gap: 6px;
  padding: 18px 14px;
  flex: 1;
  align-content: start;
}

.admin-shell__nav-item {
  position: relative;
  min-height: 48px;
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 0 14px;
  border-radius: 12px;
  border: 1px solid transparent;
  background: transparent;
  color: #cbd5e1;
  text-align: left;
}

.admin-shell__nav-item:hover,
.admin-shell__nav-item:focus-visible {
  background: rgba(255, 255, 255, 0.05);
  color: #ffffff;
}

.admin-shell__nav-item.is-active {
  background: rgba(30, 64, 175, 0.26);
  border-color: rgba(59, 130, 246, 0.34);
  color: #ffffff;
}

.admin-shell__nav-accent {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: rgba(148, 163, 184, 0.48);
  flex: 0 0 auto;
}

.admin-shell__nav-item.is-active .admin-shell__nav-accent {
  background: #f59e0b;
  box-shadow: 0 0 0 4px rgba(245, 158, 11, 0.12);
}

.admin-shell__nav-label {
  min-width: 0;
  font-size: 14px;
  font-weight: 600;
}

.admin-shell__footer {
  padding: 16px 18px 20px;
  border-top: 1px solid rgba(148, 163, 184, 0.12);
  display: grid;
  gap: 14px;
}

.admin-shell__footer-actions {
  display: grid;
  gap: 8px;
}

.admin-shell__footer-btn {
  width: 100%;
}

.admin-shell__main {
  min-width: 0;
  padding: 22px;
  display: grid;
  gap: 18px;
  align-content: start;
}

.admin-shell__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 20px 22px;
  border-radius: 18px;
}

.admin-shell__header-main {
  display: flex;
  align-items: center;
  gap: 14px;
}

.admin-shell__header h1 {
  margin: 6px 0 0;
  color: #0f172a;
  font-size: clamp(24px, 3vw, 32px);
  line-height: 1.1;
  letter-spacing: -0.04em;
}

.admin-shell__toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.admin-shell__content {
  display: grid;
  gap: 18px;
}

.admin-shell__menu-trigger {
  display: none;
  color: #334155;
  border-color: #dbe4ee;
  background: #f8fafc;
}

.admin-shell.is-collapsed {
  grid-template-columns: 88px minmax(0, 1fr);
}

.admin-shell.is-collapsed .admin-shell__brand {
  grid-template-columns: 46px 0 0;
}

.admin-shell.is-collapsed .admin-shell__brand-copy,
.admin-shell.is-collapsed .admin-shell__nav-label,
.admin-shell.is-collapsed .admin-shell__user,
.admin-shell.is-collapsed .admin-shell__footer-actions .ghost-button:first-child {
  display: none;
}

.admin-shell.is-collapsed .admin-shell__nav-item {
  justify-content: center;
  padding: 0;
}

.admin-shell.is-collapsed .admin-shell__footer {
  justify-items: center;
}

.admin-shell.is-collapsed .admin-shell__footer-btn {
  min-width: 0;
  width: 44px;
  padding: 0;
  font-size: 0;
}

.admin-shell.is-collapsed .admin-shell__footer-btn:last-child::before {
  content: "退";
  font-size: 14px;
  font-weight: 700;
}

@media (max-width: 1100px) {
  .admin-shell {
    grid-template-columns: 1fr;
  }

  .admin-shell__sidebar {
    position: fixed;
    left: 0;
    top: 0;
    bottom: 0;
    width: 280px;
    transform: translateX(-100%);
    transition: transform 180ms ease;
  }

  .admin-shell.is-mobile-open .admin-shell__sidebar {
    transform: translateX(0);
  }

  .admin-shell__menu-trigger {
    display: inline-flex;
  }

  .admin-shell__main {
    padding: 16px;
  }

  .admin-shell__header {
    padding: 16px 18px;
  }
}

@media (max-width: 720px) {
  .admin-shell__header {
    align-items: flex-start;
    flex-direction: column;
  }

  .admin-shell__toolbar {
    width: 100%;
    justify-content: flex-start;
  }
}
</style>

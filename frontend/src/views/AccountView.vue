<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import AppShell from '@/components/AppShell.vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

const nickname = ref(auth.user?.nickname || '')
const oldPassword = ref('')
const newPassword = ref('')
const profileMessage = ref('')
const passwordMessage = ref('')
const profileLoading = ref(false)
const passwordLoading = ref(false)

watch(() => auth.user?.nickname, (value) => {
  nickname.value = value || ''
})

async function saveNickname() {
  profileMessage.value = ''
  if (!nickname.value.trim()) {
    profileMessage.value = '昵称不能为空。'
    return
  }

  profileLoading.value = true
  try {
    await auth.updateNickname(nickname.value.trim())
    profileMessage.value = '昵称已更新。'
  } catch (error) {
    profileMessage.value = error instanceof Error ? error.message : '保存失败。'
  } finally {
    profileLoading.value = false
  }
}

async function savePassword() {
  passwordMessage.value = ''
  if (!oldPassword.value.trim() || !newPassword.value.trim()) {
    passwordMessage.value = '请填写旧密码和新密码。'
    return
  }

  passwordLoading.value = true
  try {
    await auth.updatePassword(oldPassword.value, newPassword.value)
    oldPassword.value = ''
    newPassword.value = ''
    passwordMessage.value = '密码已更新。'
  } catch (error) {
    passwordMessage.value = error instanceof Error ? error.message : '修改失败。'
  } finally {
    passwordLoading.value = false
  }
}

function logout() {
  auth.logout()
  router.push('/')
}
</script>

<template>
  <AppShell>
    <div class="acc-page">
      <header class="acc-header">
        <span class="acc-avatar">{{ (auth.user?.nickname || auth.user?.username || 'PA').slice(0, 2) }}</span>
        <div><h1 class="acc-title">个人中心</h1><p class="acc-sub">{{ auth.user?.nickname || auth.user?.username }} · {{ auth.user?.username }}</p></div>
      </header>
      <div class="acc-grid">
        <section class="acc-card">
          <h3 class="acc-card-title">基本资料</h3>
          <div class="acc-field"><label class="acc-label">用户名</label><input :value="auth.user?.username || ''" type="text" disabled class="acc-input" /></div>
          <div class="acc-field"><label class="acc-label">昵称</label><input v-model="nickname" type="text" maxlength="50" placeholder="输入新的昵称" class="acc-input" /></div>
          <p class="acc-msg" :class="{ 'acc-msg--ok': profileMessage === '昵称已更新。' }">{{ profileMessage }}</p>
          <button type="button" class="btn-primary" :disabled="profileLoading" @click="saveNickname">{{ profileLoading ? '保存中…' : '保存昵称' }}</button>
        </section>
        <section class="acc-card">
          <h3 class="acc-card-title">密码管理</h3>
          <div class="acc-field"><label class="acc-label">旧密码</label><input v-model="oldPassword" type="password" autocomplete="current-password" class="acc-input" /></div>
          <div class="acc-field"><label class="acc-label">新密码</label><input v-model="newPassword" type="password" autocomplete="new-password" class="acc-input" /></div>
          <p class="acc-msg" :class="{ 'acc-msg--ok': passwordMessage === '密码已更新。' }">{{ passwordMessage }}</p>
          <button type="button" class="btn-primary" :disabled="passwordLoading" @click="savePassword">{{ passwordLoading ? '提交中…' : '修改密码' }}</button>
        </section>
      </div>
      <button type="button" class="acc-logout" @click="logout">退出登录</button>
    </div>
  </AppShell>
</template>

<style scoped>
.acc-page{max-width:800px;margin:0 auto;width:100%;display:grid;gap:20px;font-family:-apple-system,BlinkMacSystemFont,"SF Pro Display","SF Pro Text","PingFang SC","Microsoft YaHei",sans-serif;}
.acc-header{display:flex;align-items:center;gap:16px;padding:20px 24px;border-radius:18px;background:#FFFFFF;border:1px solid rgba(60,60,67,0.12);box-shadow:0 1px 2px rgba(0,0,0,0.03);}
.acc-avatar{width:52px;height:52px;display:flex;align-items:center;justify-content:center;border-radius:14px;background:#007AFF;color:#fff;font-size:20px;font-weight:800;flex-shrink:0;}
.acc-title{margin:0;font-size:22px;font-weight:700;color:#000;}
.acc-sub{margin:2px 0 0;font-size:14px;color:rgba(60,60,67,0.6);}
.acc-grid{display:grid;grid-template-columns:1fr 1fr;gap:18px;}
.acc-card{padding:24px;border-radius:18px;background:#FFFFFF;border:1px solid rgba(60,60,67,0.12);box-shadow:0 1px 2px rgba(0,0,0,0.03);display:grid;gap:14px;}
.acc-card-title{margin:0;font-size:17px;font-weight:700;color:#000;}
.acc-field{display:grid;gap:6px;}
.acc-label{font-size:13px;font-weight:600;color:rgba(60,60,67,0.6);}
.acc-input{height:44px;padding:0 14px;border-radius:12px;border:1px solid rgba(60,60,67,0.18);background:#fff;font-size:15px;font-family:inherit;outline:none;transition:border-color 0.15s;}
.acc-input:focus{border-color:#007AFF;box-shadow:0 0 0 3px rgba(0,122,255,0.12);}
.acc-input:disabled{background:rgba(60,60,67,0.04);color:rgba(60,60,67,0.5);cursor:not-allowed;}
.acc-msg{min-height:20px;margin:0;font-size:13px;color:#FF3B30;font-weight:600;}
.acc-msg--ok{color:#34C759;}
.btn-primary{height:44px;padding:0 24px;border:none;border-radius:12px;background:#007AFF;color:#fff;font-size:15px;font-weight:600;font-family:inherit;cursor:pointer;justify-self:start;transition:background 0.15s;}
.btn-primary:hover:not(:disabled){background:#006EE6;}
.btn-primary:disabled{opacity:0.5;cursor:not-allowed;}
.acc-logout{height:44px;border:none;border-radius:12px;background:rgba(255,59,48,0.06);color:#FF3B30;font-size:15px;font-weight:600;font-family:inherit;cursor:pointer;transition:background 0.15s;width:100%;}
.acc-logout:hover{background:rgba(255,59,48,0.12);}
@media(max-width:640px){.acc-grid{grid-template-columns:1fr;}}
</style>

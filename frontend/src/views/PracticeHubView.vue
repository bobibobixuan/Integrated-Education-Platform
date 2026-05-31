<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import AppShell from '@/components/AppShell.vue'
import { useGameStore } from '@/stores/game'

const router = useRouter()
const game = useGameStore()

async function beginPractice() {
  await game.beginPractice()
  if (game.phase === 'practice') {
    router.push('/practice/session')
  }
}

onMounted(() => {
  void game.loadUnits()
})
</script>

<template>
  <AppShell>
    <div class="ph-page">
      <div v-if="game.error" class="ph-error">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
        <span>{{ game.error }}</span>
        <button type="button" class="ph-error-close" @click="game.error = ''">✕</button>
      </div>

      <header class="ph-header">
        <h1 class="ph-title">随机练习</h1>
        <p class="ph-desc">选择一个单元，开始连续练习和即时解析。</p>
      </header>

      <div class="ph-layout">
        <section class="ph-card">
          <h3 class="ph-card-title">练习配置</h3>
          <select v-model="game.selectedUnitId" class="ph-select">
            <option :value="null" disabled>请选择学习单元</option>
            <option v-for="unit in game.units" :key="unit.id" :value="unit.id">{{ unit.name }}</option>
          </select>
          <div class="ph-actions">
            <button type="button" class="btn-primary" :disabled="!game.selectedUnitId" @click="beginPractice">开始练习</button>
            <button type="button" class="btn-outline" @click="router.push('/')">返回首页</button>
          </div>
        </section>
        <aside class="ph-info">
          <h4>练习说明</h4>
          <p>选择单元后进入连续刷题模式，每题即时显示解析。练习进度不会影响冒险闯关。</p>
          <ul>
            <li>每题立即查看正确答案和解析</li>
            <li>可随时结束，不限次数</li>
            <li>练习统计会保留在学习记录中</li>
          </ul>
        </aside>
      </div>
    </div>
  </AppShell>
</template>

<style scoped>
.ph-page{max-width:900px;margin:0 auto;width:100%;display:grid;gap:18px;font-family:-apple-system,BlinkMacSystemFont,"SF Pro Display","SF Pro Text","PingFang SC","Microsoft YaHei",sans-serif;}
.ph-error{display:flex;align-items:center;gap:10px;padding:12px 14px;border-radius:12px;background:rgba(255,59,48,0.08);border:1px solid rgba(255,59,48,0.35);color:#FF3B30;font-size:14px;}
.ph-error span{flex:1;}
.ph-error-close{width:24px;height:24px;display:flex;align-items:center;justify-content:center;border:none;border-radius:6px;background:rgba(255,59,48,0.12);color:#FF3B30;font-size:12px;cursor:pointer;}
.ph-header{text-align:center;padding:4px 0 0;}
.ph-title{margin:0;font-size:28px;font-weight:700;color:#000;}
.ph-desc{margin:6px 0 0;font-size:14px;color:rgba(60,60,67,0.6);}
.ph-layout{display:grid;grid-template-columns:1fr 280px;gap:18px;align-items:start;}
.ph-card{padding:24px;border-radius:18px;background:#FFFFFF;border:1px solid rgba(60,60,67,0.12);box-shadow:0 1px 2px rgba(0,0,0,0.03);display:grid;gap:14px;}
.ph-card-title{margin:0;font-size:17px;font-weight:700;color:#000;}
.ph-select{width:100%;height:46px;padding:0 14px;border-radius:12px;border:1px solid rgba(60,60,67,0.18);background:#FFFFFF;font-size:15px;font-family:inherit;color:#000;outline:none;cursor:pointer;appearance:none;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%23666' stroke-width='2'%3E%3Cpolyline points='6 9 12 15 18 9'/%3E%3C/svg%3E");background-repeat:no-repeat;background-position:right 14px center;padding-right:36px;}
.ph-select:focus{border-color:#007AFF;box-shadow:0 0 0 3px rgba(0,122,255,0.12);}
.ph-actions{display:flex;gap:12px;}
.btn-primary{height:46px;padding:0 28px;border:none;border-radius:12px;background:#007AFF;color:#fff;font-size:15px;font-weight:600;font-family:inherit;cursor:pointer;transition:background 0.15s;}
.btn-primary:hover:not(:disabled){background:#006EE6;}
.btn-primary:disabled{opacity:0.45;cursor:not-allowed;}
.btn-outline{height:46px;padding:0 28px;border:1px solid rgba(60,60,67,0.2);border-radius:12px;background:#fff;color:#000;font-size:15px;font-weight:600;font-family:inherit;cursor:pointer;}
.btn-outline:hover{border-color:#007AFF;background:rgba(0,122,255,0.04);}
.ph-info{padding:20px;border-radius:16px;background:#FFFFFF;border:1px solid rgba(60,60,67,0.12);box-shadow:0 1px 2px rgba(0,0,0,0.03);}
.ph-info h4{margin:0 0 8px;font-size:15px;font-weight:700;color:#000;}
.ph-info p{margin:0 0 12px;font-size:13px;color:rgba(60,60,67,0.6);line-height:1.5;}
.ph-info ul{margin:0;padding:0 0 0 16px;display:grid;gap:6px;}
.ph-info li{font-size:13px;color:rgba(60,60,67,0.6);line-height:1.4;}
@media(max-width:700px){.ph-layout{grid-template-columns:1fr;}}
</style>

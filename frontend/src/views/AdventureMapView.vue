<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import AppShell from '@/components/AppShell.vue'
import { useGameStore } from '@/stores/game'
import type { LevelOut } from '@/types/api'

const router = useRouter()
const game = useGameStore()

const selectedUnit = computed(() => game.units.find(unit => unit.id === game.selectedUnitId) || null)
const selectedLevel = computed(() => {
  const unit = selectedUnit.value
  if (!unit || !Array.isArray(unit.levels)) return null
  return unit.levels.find(level => level.id === game.selectedLevelId) || null
})
const selectedLevels = computed<LevelOut[]>(() => {
  if (!selectedUnit.value || !Array.isArray(selectedUnit.value.levels)) return []
  return selectedUnit.value.levels
})

const selectedUnitMark = computed(() => {
  const name = selectedUnit.value?.name?.trim()
  return name ? name.slice(0, 1) : '课'
})

function onUnitChange() {
  if (!game.selectedUnitId) return
  const unit = game.units.find(u => u.id === game.selectedUnitId)
  if (!unit || !Array.isArray(unit.levels) || unit.levels.length === 0) return
  game.selectLevel(unit.id, unit.levels[0].id)
}

function onSelectLevel(unitId: number, levelId: number) {
  game.selectLevel(unitId, levelId)
}

async function beginAdventure() {
  await game.beginLevel()
  if (game.phase === 'playing') {
    router.push('/adventure/play')
  }
}

onMounted(() => {
  void game.loadUnits()
})
</script>

<template>
  <AppShell>
    <div class="adv-page">
      <!-- Error -->
      <div v-if="game.error" class="adv-error">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
        <span>{{ game.error }}</span>
        <button type="button" class="adv-error-close" @click="game.error = ''">✕</button>
      </div>

      <!-- Title -->
      <header class="adv-header">
        <h1 class="adv-title">冒险地图</h1>
        <p class="adv-desc">选择学习单元和关卡，开始当前阶段的挑战。</p>
      </header>

      <!-- Loading -->
      <div v-if="game.loading && game.units.length === 0" class="adv-loading">正在加载学习地图…</div>

      <!-- Main Layout -->
      <div v-else class="adv-layout">
        <!-- Left: Unit Dropdown -->
        <aside class="adv-left">
          <h3 class="adv-section-title">学习单元</h3>
          <select v-model="game.selectedUnitId" class="adv-select" @change="onUnitChange">
            <option :value="null" disabled>请选择学习单元</option>
            <option v-for="unit in game.units" :key="unit.id" :value="unit.id">{{ unit.name }}</option>
          </select>
        </aside>

        <!-- Right: Level Selection -->
        <section class="adv-right">
          <div v-if="!selectedUnit" class="adv-card adv-card--empty">
            <h3>选择学习单元</h3>
            <p>从左侧列表中选择一个单元，然后挑选关卡开始挑战。</p>
          </div>

          <template v-else>
            <!-- Unit Info -->
            <div class="adv-card">
              <div class="adv-unit-head">
                <span class="adv-unit-icon">{{ selectedUnitMark }}</span>
                <div>
                  <h3>{{ selectedUnit.name }}</h3>
                  <p>{{ selectedUnit.learning_goal || selectedUnit.description }}</p>
                </div>
              </div>
            </div>

            <!-- Levels -->
            <div class="adv-card">
              <h4 class="adv-card-label">选择关卡</h4>
              <div class="level-grid">
                <button
                  v-for="level in selectedLevels"
                  :key="level.id"
                  type="button"
                  class="level-item"
                  :class="{ 'level-item--sel': game.selectedLevelId === level.id }"
                  @click="onSelectLevel(selectedUnit.id, level.id)"
                >
                  <strong>{{ level.name }}</strong>
                  <span>{{ level.questions }} 题</span>
                </button>
              </div>

              <!-- Summary -->
              <div class="adv-summary">
                <span>单元：{{ selectedUnit.name }}</span>
                <span>关卡：{{ selectedLevel?.name || '未选择' }}</span>
                <span>题量：{{ selectedLevel?.questions || 0 }}</span>
              </div>

              <!-- Actions -->
              <div class="adv-actions">
                <button type="button" class="btn-primary" :disabled="!game.selectedLevelId" @click="beginAdventure">进入作答页</button>
                <button type="button" class="btn-outline" @click="router.push('/records')">学习记录</button>
              </div>
            </div>
          </template>
        </section>
      </div>
    </div>
  </AppShell>
</template>

<style scoped>
/* ── Shell ── */
.adv-page { max-width:1100px; margin:0 auto; width:100%; display:grid; gap:18px; font-family:-apple-system,BlinkMacSystemFont,"SF Pro Display","SF Pro Text","PingFang SC","Microsoft YaHei",sans-serif; }

/* ── Error ── */
.adv-error{display:flex;align-items:center;gap:10px;padding:12px 14px;border-radius:12px;background:rgba(255,59,48,0.08);border:1px solid rgba(255,59,48,0.35);color:#FF3B30;font-size:14px;}
.adv-error span{flex:1;}
.adv-error-close{width:24px;height:24px;display:flex;align-items:center;justify-content:center;border:none;border-radius:6px;background:rgba(255,59,48,0.12);color:#FF3B30;font-size:12px;cursor:pointer;}

/* ── Header ── */
.adv-header{text-align:center;padding:4px 0 0;}
.adv-title{margin:0;font-size:28px;font-weight:700;color:#000;}
.adv-desc{margin:6px 0 0;font-size:14px;color:rgba(60,60,67,0.6);}
.adv-loading{text-align:center;padding:40px;color:rgba(60,60,67,0.6);}
.adv-empty{text-align:center;padding:20px;color:rgba(60,60,67,0.45);font-size:14px;}
.adv-section-title{margin:0 0 10px;font-size:16px;font-weight:700;color:#000;}

/* ── Layout ── */
.adv-layout{display:grid;grid-template-columns:300px 1fr;gap:20px;align-items:start;}
.adv-left{display:grid;gap:4px;}
.adv-right{display:grid;gap:16px;}

/* ── Unit Dropdown ── */
.adv-select{width:100%;height:46px;padding:0 14px;border-radius:12px;border:1px solid rgba(60,60,67,0.18);background:#FFFFFF;font-size:15px;font-family:inherit;color:#000;outline:none;cursor:pointer;appearance:none;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%23666' stroke-width='2'%3E%3Cpolyline points='6 9 12 15 18 9'/%3E%3C/svg%3E");background-repeat:no-repeat;background-position:right 14px center;padding-right:36px;}
.adv-select:focus{border-color:#007AFF;box-shadow:0 0 0 3px rgba(0,122,255,0.12);}

/* ── Right Cards ── */
.adv-card{padding:24px;border-radius:18px;background:#FFFFFF;border:1px solid rgba(60,60,67,0.12);box-shadow:0 1px 2px rgba(0,0,0,0.03);}
.adv-card--empty{text-align:center;padding:40px 24px;}
.adv-card--empty h3{margin:0 0 8px;font-size:18px;font-weight:700;color:#000;}
.adv-card--empty p{margin:0;font-size:14px;color:rgba(60,60,67,0.6);}
.adv-card-label{margin:0 0 12px;font-size:15px;font-weight:700;color:#000;}

/* ── Unit Head ── */
.adv-unit-head{display:flex;align-items:flex-start;gap:14px;}
.adv-unit-icon{width:48px;height:48px;display:flex;align-items:center;justify-content:center;border-radius:12px;background:rgba(0,122,255,0.08);font-size:18px;font-weight:700;color:#007AFF;flex-shrink:0;}
.adv-unit-head h3{margin:0 0 4px;font-size:20px;font-weight:700;color:#000;}
.adv-unit-head p{margin:0;font-size:13px;color:rgba(60,60,67,0.6);line-height:1.5;}

/* ── Level Grid ── */
.level-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:8px;margin-bottom:16px;}
.level-item{
  display:flex;flex-direction:column;gap:4px;padding:14px 16px;border-radius:12px;
  border:1px solid rgba(60,60,67,0.12);background:#FFFFFF;text-align:left;
  font-family:inherit;cursor:pointer;transition:border-color 0.15s,background 0.15s;
}
.level-item:hover{border-color:rgba(0,122,255,0.35);}
.level-item--sel{border-color:#007AFF;background:rgba(0,122,255,0.04);}
.level-item strong{font-size:15px;font-weight:600;color:#000;}
.level-item span{font-size:12px;color:rgba(60,60,67,0.5);}

/* ── Summary ── */
.adv-summary{display:flex;flex-wrap:wrap;gap:16px;padding:14px 0;border-top:1px solid rgba(60,60,67,0.1);margin-bottom:4px;font-size:13px;color:rgba(60,60,67,0.6);}

/* ── Actions ── */
.adv-actions{display:flex;gap:12px;}
.btn-primary{height:46px;padding:0 28px;border:none;border-radius:12px;background:#007AFF;color:#fff;font-size:15px;font-weight:600;font-family:inherit;cursor:pointer;transition:background 0.15s;}
.btn-primary:hover:not(:disabled){background:#006EE6;}
.btn-primary:disabled{opacity:0.5;cursor:not-allowed;}
.btn-outline{height:46px;padding:0 28px;border:1px solid rgba(60,60,67,0.2);border-radius:12px;background:#fff;color:#000;font-size:15px;font-weight:600;font-family:inherit;cursor:pointer;transition:border-color 0.15s;}
.btn-outline:hover{border-color:#007AFF;background:rgba(0,122,255,0.04);}

/* ── Responsive ── */
@media(max-width:768px){
  .adv-layout{grid-template-columns:1fr;}
  .level-grid{grid-template-columns:1fr 1fr;}
  .adv-actions{flex-direction:column;}
  .btn-primary,.btn-outline{width:100%;}
}
</style>

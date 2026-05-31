<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import AppShell from '@/components/AppShell.vue'
import { useAuthStore } from '@/stores/auth'
import {
  fetchRecordSummary,
  fetchScoreProgress,
  fetchScoreStats,
  fetchWrongQuestionRecords,
} from '@/api/records'
import type { RecordSummary, ScoreProgressUnit, ScoreStats, WrongQuestionRecord } from '@/types/api'

const router = useRouter()
const auth = useAuthStore()
const loading = ref(false)
const error = ref('')
const summary = ref<RecordSummary | null>(null)
const stats = ref<ScoreStats | null>(null)
const progress = ref<ScoreProgressUnit[]>([])
const wrongQuestions = ref<WrongQuestionRecord[]>([])

const totalStars = computed(() => {
  return progress.value.reduce((sum, unit) => {
    return sum + unit.levels.reduce((levelSum, level) => levelSum + (level.stars || 0), 0)
  }, 0)
})

const weakestUnits = computed(() => {
  const unitMap = new Map<string, number>()
  for (const item of wrongQuestions.value) {
    unitMap.set(item.unit_name, (unitMap.get(item.unit_name) || 0) + 1)
  }
  return [...unitMap.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 4)
})

function unitMark(name: string) {
  const text = name.trim()
  return text ? text.slice(0, 1) : '课'
}

async function loadRecords() {
  if (!auth.token) return

  loading.value = true
  error.value = ''
  try {
    const [summaryRes, statsRes, progressRes, wrongRes] = await Promise.all([
      fetchRecordSummary(auth.token),
      fetchScoreStats(auth.token),
      fetchScoreProgress(auth.token),
      fetchWrongQuestionRecords(auth.token),
    ])
    summary.value = summaryRes
    stats.value = statsRes
    progress.value = progressRes
    wrongQuestions.value = wrongRes
  } catch (e: unknown) {
    error.value = (e as Error).message
  } finally {
    loading.value = false
  }
}

function levelStatusText(stars: number, unlocked: boolean) {
  if (!unlocked) return '未解锁'
  if (!stars) return '已解锁'
  return `${stars} 星`
}

onMounted(() => {
  if (!auth.isAuthenticated) return
  loadRecords()
})
</script>

<template>
  <AppShell title="学习记录">
    <div class="rec-page">
      <!-- Error -->
      <div v-if="error" class="rec-error">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
        <span>{{ error }}</span>
        <button type="button" class="rec-error-close" @click="error = ''">✕</button>
      </div>

      <!-- Unauthenticated -->
      <section v-if="!auth.isAuthenticated" class="rec-empty-card">
        <h2>先登录，再查看你的学习档案</h2>
        <p>记录页会展示做题量、错题、各单元进度和挑战荣誉。</p>
        <div class="rec-empty-btns">
          <button type="button" class="btn-primary" @click="router.push('/login')">去登录</button>
          <button type="button" class="btn-ghost" @click="router.push('/')">返回首页</button>
        </div>
      </section>

      <div v-else-if="loading" class="rec-loading">正在加载学习档案…</div>

      <template v-else>
        <!-- Title -->
        <header class="rec-header">
          <h1 class="rec-title">学习记录</h1>
          <p class="rec-desc">做题量、错题复盘、各单元进度和挑战荣誉一览。</p>
        </header>

        <!-- Row 1: Stats + Badges -->
        <div class="rec-overview">
          <div class="rec-stats">
            <div class="stat-card"><span class="stat-label">总做题数</span><strong class="stat-val">{{ summary?.total_questions ?? 0 }}</strong></div>
            <div class="stat-card"><span class="stat-label">正确题数</span><strong class="stat-val stat-val--ok">{{ summary?.total_correct ?? 0 }}</strong></div>
            <div class="stat-card"><span class="stat-label">正确率</span><strong class="stat-val stat-val--blue">{{ stats ? Math.round(stats.accuracy) : 0 }}%</strong></div>
            <div class="stat-card"><span class="stat-label">累计星级</span><strong class="stat-val stat-val--warn">{{ totalStars }}</strong></div>
          </div>
          <div class="rec-badges">
            <h3 class="rec-section-title">荣誉徽章</h3>
            <div class="badge-row">
              <div class="badge-item">
                <span class="badge-icon badge-icon--gold" aria-hidden="true">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                    <path d="M12 4L14.4 8.6L19.5 9.3L15.8 12.9L16.7 18L12 15.6L7.3 18L8.2 12.9L4.5 9.3L9.6 8.6L12 4Z" fill="currentColor"/>
                  </svg>
                </span>
                <strong>{{ summary?.extreme_passes ?? 0 }}</strong>
                <small>极限通关</small>
              </div>
              <div class="badge-item">
                <span class="badge-icon badge-icon--blue" aria-hidden="true">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                    <path d="M7 5H17V8C17 11.3 14.8 14.2 12 15C9.2 14.2 7 11.3 7 8V5Z" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/>
                    <path d="M9 18H15" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
                    <path d="M10 21H14" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
                  </svg>
                </span>
                <strong>{{ summary?.extreme_dual_passes ?? 0 }}</strong>
                <small>双单元</small>
              </div>
              <div class="badge-item">
                <span class="badge-icon badge-icon--green" aria-hidden="true">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                    <path d="M12 5C9.5 7.2 8 9.6 8 12.2C8 15 9.8 17 12 17C14.2 17 16 15 16 12.2C16 9.6 14.5 7.2 12 5Z" stroke="currentColor" stroke-width="1.8"/>
                    <path d="M12 17V20" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
                  </svg>
                </span>
                <strong>{{ summary?.practice_count ?? 0 }}</strong>
                <small>修炼场</small>
              </div>
              <div class="badge-item">
                <span class="badge-icon badge-icon--orange" aria-hidden="true">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                    <path d="M13 3L6 13H11L10 21L18 10H13L13 3Z" fill="currentColor"/>
                  </svg>
                </span>
                <strong>{{ summary?.power_score ?? 0 }}</strong>
                <small>战力</small>
              </div>
            </div>
          </div>
        </div>

        <!-- Row 2: Unit Progress -->
        <section class="rec-section">
          <h3 class="rec-section-title">分单元关卡进度</h3>
          <div v-if="progress.length === 0" class="rec-empty">暂无关卡进度。</div>
          <div v-else class="progress-grid">
            <article v-for="unit in progress" :key="unit.unit_id" class="prog-card">
              <div class="prog-card-head">
                <span class="prog-icon">{{ unitMark(unit.unit_name) }}</span>
                <div><strong>{{ unit.unit_name }}</strong><small>{{ unit.levels.length }} 个关卡</small></div>
              </div>
              <div class="prog-levels">
                <span v-for="level in unit.levels" :key="level.level_id" class="prog-level" :class="{ 'prog-level--locked': !level.unlocked }">
                  {{ level.name }} <small>{{ levelStatusText(level.stars, level.unlocked) }}</small>
                </span>
              </div>
            </article>
          </div>
        </section>

        <!-- Row 3: Review -->
        <div class="rec-review">
          <section class="rec-card">
            <h3 class="rec-section-title">学习画像</h3>
            <div class="profile-grid">
              <div class="profile-item"><span>最高连击</span><strong>{{ summary?.max_combo ?? 0 }}</strong></div>
              <div class="profile-item"><span>累计得分</span><strong>{{ summary?.total_score ?? 0 }}</strong></div>
              <div class="profile-item"><span>当前战力</span><strong>{{ summary?.power_score ?? 0 }}</strong></div>
              <div class="profile-item"><span>错题数</span><strong>{{ wrongQuestions.length }}</strong></div>
            </div>
            <div class="weak-box">
              <h4>高频失分单元</h4>
              <div v-if="weakestUnits.length === 0" class="weak-empty">暂无薄弱单元。</div>
              <div v-else class="weak-list">
                <span v-for="[unitName, count] in weakestUnits" :key="unitName" class="weak-chip">{{ unitName }} {{ count }}题</span>
              </div>
            </div>
          </section>

          <section class="rec-card">
            <h3 class="rec-section-title">最近错题</h3>
            <div v-if="wrongQuestions.length === 0" class="rec-empty">暂无错题记录。</div>
            <div v-else class="wrong-list">
              <article v-for="item in wrongQuestions.slice(0, 10)" :key="item.id" class="wrong-item">
                <p class="wrong-q">{{ item.question_content }}</p>
                <div class="wrong-meta">
                  <span>{{ item.unit_name }} / {{ item.level_name }}</span>
                  <span class="wrong-user">你的答案：{{ item.user_answer || '空' }}</span>
                  <span class="wrong-correct">正确答案：{{ item.correct_answer }}</span>
                </div>
              </article>
            </div>
          </section>
        </div>

        <!-- Bottom Actions -->
        <div class="rec-actions">
          <button type="button" class="btn-primary" @click="loadRecords()">刷新档案</button>
          <button type="button" class="btn-outline" @click="router.push('/game')">回到闯关</button>
        </div>
      </template>
    </div>
  </AppShell>
</template>

<style scoped>
/* ── Shell ── */
.rec-page {
  min-height: 100vh; background: #F2F2F7; padding-bottom: 40px;
  width:100%;
  display:grid; gap:20px;
  font-family:-apple-system,BlinkMacSystemFont,"SF Pro Display","SF Pro Text","PingFang SC","Microsoft YaHei",sans-serif;
}

/* ── Error ── */
.rec-error{display:flex;align-items:center;gap:10px;padding:12px 14px;border-radius:12px;background:rgba(255,59,48,0.08);border:1px solid rgba(255,59,48,0.35);color:#FF3B30;font-size:14px;}
.rec-error span{flex:1;}
.rec-error-close{width:24px;height:24px;display:flex;align-items:center;justify-content:center;border:none;border-radius:6px;background:rgba(255,59,48,0.12);color:#FF3B30;font-size:12px;cursor:pointer;}

/* ── Unauthenticated ── */
.rec-empty-card{text-align:center;padding:60px 32px;border-radius:18px;background:#FFFFFF;border:1px solid rgba(60,60,67,0.12);box-shadow:0 1px 2px rgba(0,0,0,0.04),0 8px 24px rgba(0,0,0,0.05);}
.rec-empty-card h2{margin:0 0 8px;font-size:22px;font-weight:700;color:#000;}
.rec-empty-card p{margin:0 0 24px;font-size:14px;color:rgba(60,60,67,0.6);}
.rec-empty-btns{display:flex;gap:12px;justify-content:center;flex-wrap:wrap;}
.rec-loading{text-align:center;padding:40px;color:rgba(60,60,67,0.6);font-size:14px;}
.rec-empty{text-align:center;padding:20px;color:rgba(60,60,67,0.45);font-size:14px;}

/* ── Header ── */
.rec-header{text-align:center;padding:8px 0 0;}
.rec-title{margin:0;font-size:30px;font-weight:700;color:#000;}
.rec-desc{margin:6px 0 0;font-size:14px;color:rgba(60,60,67,0.6);}
.rec-section-title{margin:0 0 10px;font-size:18px;font-weight:700;color:#000;}

/* ── Overview ── */
.rec-overview{display:grid;grid-template-columns:1fr 280px;gap:20px;align-items:start;}
.rec-stats{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;}
.stat-card{padding:20px 14px;text-align:center;border-radius:16px;background:#FFF;border:1px solid rgba(60,60,67,0.12);box-shadow:0 1px 2px rgba(0,0,0,0.03);}
.stat-label{display:block;font-size:12px;color:rgba(60,60,67,0.45);text-transform:uppercase;letter-spacing:0.04em;margin-bottom:6px;}
.stat-val{font-size:28px;font-weight:800;color:#000;}
.stat-val--ok{color:#34C759;}
.stat-val--blue{color:#007AFF;}
.stat-val--warn{color:#FF9500;}
.rec-badges{padding:20px;border-radius:16px;background:#FFF;border:1px solid rgba(60,60,67,0.12);box-shadow:0 1px 2px rgba(0,0,0,0.03);}
.badge-row{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:4px;}
.badge-item{display:flex;align-items:center;gap:8px;padding:10px 12px;border-radius:10px;background:rgba(0,122,255,0.04);}
.badge-icon{
  width:28px;
  height:28px;
  display:flex;
  align-items:center;
  justify-content:center;
  border-radius:9px;
  flex-shrink:0;
}
.badge-icon--gold{background:rgba(255,149,0,0.12);color:#FF9500;}
.badge-icon--blue{background:rgba(0,122,255,0.12);color:#007AFF;}
.badge-icon--green{background:rgba(52,199,89,0.12);color:#34C759;}
.badge-icon--orange{background:rgba(255,59,48,0.12);color:#FF3B30;}
.badge-item strong{font-size:16px;font-weight:700;color:#000;}
.badge-item small{font-size:11px;color:rgba(60,60,67,0.5);margin-left:auto;}

/* ── Unit Progress ── */
.rec-section{padding:24px;border-radius:18px;background:#FFF;border:1px solid rgba(60,60,67,0.12);box-shadow:0 1px 2px rgba(0,0,0,0.03);}
.progress-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:14px;}
.prog-card{padding:18px;border-radius:14px;border:1px solid rgba(60,60,67,0.1);background:#FFF;}
.prog-card-head{display:flex;align-items:center;gap:10px;margin-bottom:10px;}
.prog-icon{width:38px;height:38px;display:flex;align-items:center;justify-content:center;border-radius:10px;background:rgba(0,122,255,0.08);font-size:14px;font-weight:700;color:#007AFF;flex-shrink:0;}
.prog-card-head strong{font-size:15px;color:#000;}
.prog-card-head small{display:block;font-size:12px;color:rgba(60,60,67,0.5);}
.prog-levels{display:flex;flex-wrap:wrap;gap:6px;}
.prog-level{padding:4px 10px;border-radius:8px;background:rgba(0,122,255,0.05);font-size:13px;color:#000;}
.prog-level small{color:#FF9500;font-weight:700;}
.prog-level--locked{opacity:0.4;}

/* ── Review ── */
.rec-review{display:grid;grid-template-columns:1fr 1fr;gap:20px;}
.rec-card{padding:24px;border-radius:18px;background:#FFF;border:1px solid rgba(60,60,67,0.12);box-shadow:0 1px 2px rgba(0,0,0,0.03);}
.profile-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:16px;}
.profile-item{display:flex;justify-content:space-between;align-items:center;padding:12px 14px;border-radius:10px;background:rgba(60,60,67,0.03);}
.profile-item span{font-size:14px;color:rgba(60,60,67,0.6);}
.profile-item strong{font-size:16px;font-weight:700;color:#000;}
.weak-box h4{margin:0 0 8px;font-size:14px;font-weight:700;color:#000;}
.weak-empty{font-size:13px;color:rgba(60,60,67,0.45);}
.weak-list{display:flex;flex-wrap:wrap;gap:6px;}
.weak-chip{padding:5px 12px;border-radius:999px;font-size:12px;font-weight:600;background:rgba(255,59,48,0.06);color:#FF3B30;border:1px solid rgba(255,59,48,0.15);}

/* ── Wrong Questions ── */
.wrong-list{
  display:grid;
  gap:10px;
  max-height:420px;
  overflow-y:auto;
  padding-right:4px;
  scrollbar-gutter:stable;
}
.wrong-item{padding:14px 16px;border-radius:12px;border:1px solid rgba(60,60,67,0.08);background:#FFF;}
.wrong-q{margin:0 0 10px;font-size:14px;color:#000;line-height:1.5;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;}
.wrong-meta{display:flex;flex-wrap:wrap;gap:10px;font-size:12px;}
.wrong-meta span{color:rgba(60,60,67,0.5);}
.wrong-user{color:#FF3B30!important;font-weight:600;}
.wrong-correct{color:#34C759!important;font-weight:600;}

/* ── Buttons ── */
.btn-primary{height:44px;padding:0 24px;border:none;border-radius:12px;background:#007AFF;color:#fff;font-size:15px;font-weight:600;font-family:inherit;cursor:pointer;transition:background 0.15s,transform 0.1s;}
.btn-primary:hover{background:#006EE6;}
.btn-primary:active{transform:scale(0.98);}
.btn-outline{height:44px;padding:0 24px;border:1px solid rgba(60,60,67,0.2);border-radius:12px;background:#fff;color:#000;font-size:15px;font-weight:600;font-family:inherit;cursor:pointer;transition:border-color 0.15s,background 0.15s;}
.btn-outline:hover{border-color:#007AFF;background:rgba(0,122,255,0.04);}
.btn-ghost{height:44px;padding:0 20px;border:none;border-radius:12px;background:transparent;color:rgba(60,60,67,0.6);font-size:14px;font-weight:500;font-family:inherit;cursor:pointer;}
.btn-ghost:hover{color:#007AFF;background:rgba(0,122,255,0.04);}
.rec-actions{display:flex;gap:12px;justify-content:center;padding-bottom:8px;}

/* ── Responsive ── */
@media(max-width:900px){
  .rec-overview{grid-template-columns:1fr;}
  .rec-review{grid-template-columns:1fr;}
  .progress-grid{grid-template-columns:1fr;}
}
@media(max-width:640px){
  .rec-stats{grid-template-columns:repeat(2,1fr);}
  .badge-row{grid-template-columns:1fr;}
}
</style>

import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { fetchDashboard, getRegistrationSetting, updateRegistrationSetting } from '@/api/admin'
import { fetchUnits } from '@/api/game'
import { fetchLeaderboard } from '@/api/leaderboard'
import type { AdminDashboardOut, LeaderboardEntry, UnitOut } from '@/types/api'

const ADMIN_TOKEN_KEY = 'admin_token'
const LEGACY_ADMIN_TOKEN_KEY = 'admin_jwt_token'

type BarTone = 'blue' | 'amber' | 'red' | 'green'

interface BarItem {
  label: string
  value: number
  hint?: string
  tone?: BarTone
}

function readAdminToken() {
  return localStorage.getItem(ADMIN_TOKEN_KEY) || localStorage.getItem(LEGACY_ADMIN_TOKEN_KEY)
}

function formatNumber(value: number | null | undefined) {
  return new Intl.NumberFormat('zh-CN').format(Number(value ?? 0))
}

function formatPercent(value: number | null | undefined) {
  const number = Number(value ?? 0)
  return `${number.toFixed(number % 1 === 0 ? 0 : 1)}%`
}

function formatSeconds(value: number | null | undefined) {
  const number = Number(value ?? 0)
  return `${number.toFixed(number % 1 === 0 ? 0 : 1)}s`
}

function formatDateTime(value: string | null | undefined) {
  if (!value) return '暂无记录'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}

function getErrorMessage(error: unknown) {
  return error instanceof Error ? error.message : '加载仪表盘失败，请稍后重试。'
}

export const useAdminDashboardStore = defineStore('adminDashboard', () => {
  const loading = ref(false)
  const registrationSaving = ref(false)
  const error = ref('')
  const dashboard = ref<AdminDashboardOut | null>(null)
  const allowSelfRegister = ref(false)
  const leaderboard = ref<LeaderboardEntry[]>([])
  const leaderboardType = ref<'power' | 'weekly'>('power')
  const leaderboardLoading = ref(false)
  const selectedLeaderboardUserId = ref<number | null>(null)
  const units = ref<UnitOut[]>([])
  const lastLoadedAt = ref<string | null>(null)

  const hasData = computed(() => Boolean(dashboard.value))

  const kpis = computed(() => {
    if (!dashboard.value) return []
    return [
      { label: '学生总数', value: formatNumber(dashboard.value.user_count), hint: `活跃 ${formatNumber(dashboard.value.active_student_count)}` },
      { label: '累计作答', value: formatNumber(dashboard.value.answer_count), hint: `题库 ${formatNumber(dashboard.value.question_count)} 题` },
      { label: '平均正确率', value: formatPercent(dashboard.value.avg_accuracy), hint: `错题率 ${formatPercent(dashboard.value.wrong_rate)}` },
      { label: '平均战力', value: formatNumber(dashboard.value.avg_power_score), hint: `总战力 ${formatNumber(dashboard.value.total_power_score)}` },
      { label: '完成率', value: formatPercent(dashboard.value.completion_rate), hint: `周活跃 ${dashboard.value.avg_weekly_activity.toFixed(1)} 分钟/人` },
      { label: '待激活学生', value: formatNumber(dashboard.value.never_practiced_count), hint: `禁用 ${formatNumber(dashboard.value.disabled_student_count)}` },
    ]
  })

  const trendPoints = computed(() => (
    dashboard.value?.hourly_trend.map(item => ({ label: item.date, value: item.count })) ?? []
  ))

  const unitAccuracyBars = computed<BarItem[]>(() => (
    dashboard.value?.unit_accuracy.map(unit => ({
      label: unit.unit_name,
      value: Math.round(unit.accuracy),
      hint: `${formatPercent(unit.accuracy)} 正确率`,
      tone: 'blue',
    })) ?? []
  ))

  const weakestUnitBars = computed<BarItem[]>(() => (
    dashboard.value?.weakest_units.map(unit => ({
      label: unit.unit_name,
      value: Math.round(unit.wrong_rate ?? 0),
      hint: `${formatPercent(unit.accuracy)} 正确率 / ${formatSeconds(unit.avg_time_spent)} 平均耗时`,
      tone: 'amber',
    })) ?? []
  ))

  const topStudentBars = computed<BarItem[]>(() => {
    const dashboardStudents = dashboard.value?.top_students.map(student => ({
      label: student.nickname,
      value: student.power_score ?? 0,
      hint: `${formatPercent(student.accuracy)} 正确率 / ${formatNumber(student.total_questions)} 题`,
      tone: 'green' as const,
    })) ?? []

    if (dashboardStudents.length > 0) return dashboardStudents

    return leaderboard.value.slice(0, 5).map(student => ({
      label: student.nickname,
      value: student.power_score,
      hint: `${formatPercent(student.accuracy)} 正确率 / 第 ${student.rank} 名`,
      tone: 'green' as const,
    }))
  })

  const inactiveStudents = computed(() => dashboard.value?.inactive_students ?? [])
  const selectedLeaderboardEntry = computed(() => (
    leaderboard.value.find(item => item.user_id === selectedLeaderboardUserId.value) ?? null
  ))

  const quickLinks = computed(() => [
    {
      label: '学生管理',
      path: '/admin/students',
      desc: '查看详情、修改昵称、重置密码和批量导入。',
      meta: `${formatNumber(dashboard.value?.user_count)} 人`,
    },
    {
      label: '题库管理',
      path: '/admin/questions',
      desc: '按单元、类型和状态筛题，维护题干与知识点。',
      meta: `${formatNumber(dashboard.value?.question_count)} 题`,
    },
    {
      label: '教学分析',
      path: '/admin/analytics',
      desc: '查看单元分析、错题统计和薄弱环节。',
      meta: `${formatNumber(units.value.length)} 个单元`,
    },
    {
      label: 'PVP 管理',
      path: '/admin/pvp',
      desc: '创建房间、分配题量和控制比赛。',
      meta: '竞技房间',
    },
  ])

  async function loadDashboard() {
    const token = readAdminToken()
    if (!token) {
      dashboard.value = null
      error.value = '请先登录教师管理后台。'
      return
    }

    loading.value = true
    error.value = ''
    try {
      const [dashboardRes, registrationRes, leaderboardRes, unitsRes] = await Promise.all([
        fetchDashboard(token),
        getRegistrationSetting(token),
        fetchLeaderboard(token, leaderboardType.value, 50),
        fetchUnits(token),
      ])
      dashboard.value = dashboardRes
      allowSelfRegister.value = registrationRes.allow_self_register
      leaderboard.value = leaderboardRes.entries
      if (!leaderboard.value.some(item => item.user_id === selectedLeaderboardUserId.value)) {
        selectedLeaderboardUserId.value = leaderboard.value[0]?.user_id ?? null
      }
      units.value = unitsRes
      lastLoadedAt.value = new Date().toISOString()
    } catch (err) {
      error.value = getErrorMessage(err)
    } finally {
      loading.value = false
    }
  }

  async function loadLeaderboard(type = leaderboardType.value) {
    const token = readAdminToken()
    if (!token) {
      error.value = '请先登录教师管理后台。'
      return
    }

    leaderboardType.value = type
    leaderboardLoading.value = true
    error.value = ''
    try {
      const res = await fetchLeaderboard(token, type, 50)
      leaderboard.value = res.entries
      if (!leaderboard.value.some(item => item.user_id === selectedLeaderboardUserId.value)) {
        selectedLeaderboardUserId.value = leaderboard.value[0]?.user_id ?? null
      }
    } catch (err) {
      error.value = getErrorMessage(err)
    } finally {
      leaderboardLoading.value = false
    }
  }

  async function setAllowSelfRegister(value: boolean) {
    const token = readAdminToken()
    if (!token) {
      error.value = '请先登录教师管理后台。'
      allowSelfRegister.value = !value
      return
    }

    const previous = allowSelfRegister.value
    allowSelfRegister.value = value
    registrationSaving.value = true
    error.value = ''
    try {
      const res = await updateRegistrationSetting(token, value)
      allowSelfRegister.value = res.allow_self_register
    } catch (err) {
      allowSelfRegister.value = previous
      error.value = getErrorMessage(err)
    } finally {
      registrationSaving.value = false
    }
  }

  return {
    loading,
    registrationSaving,
    error,
    dashboard,
    allowSelfRegister,
    leaderboard,
    leaderboardType,
    leaderboardLoading,
    selectedLeaderboardUserId,
    selectedLeaderboardEntry,
    units,
    lastLoadedAt,
    hasData,
    kpis,
    trendPoints,
    unitAccuracyBars,
    weakestUnitBars,
    topStudentBars,
    inactiveStudents,
    quickLinks,
    formatNumber,
    formatPercent,
    formatDateTime,
    loadDashboard,
    loadLeaderboard,
    setAllowSelfRegister,
  }
})

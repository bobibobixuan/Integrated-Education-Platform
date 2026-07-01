import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { fetchLevelAnalytics, fetchWrongQuestionStats } from '@/api/admin'
import { fetchUnits } from '@/api/game'
import type { AdminLevelAnalyticsItem, AdminWrongQuestionItem, LevelOut, UnitOut } from '@/types/api'

const ADMIN_TOKEN_KEY = 'admin_token'
const LEGACY_ADMIN_TOKEN_KEY = 'admin_jwt_token'

function readAdminToken() {
  return localStorage.getItem(ADMIN_TOKEN_KEY) || localStorage.getItem(LEGACY_ADMIN_TOKEN_KEY)
}

function getErrorMessage(error: unknown) {
  return error instanceof Error ? error.message : '加载分析数据失败，请稍后重试。'
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

export const useAdminAnalyticsStore = defineStore('adminAnalytics', () => {
  const activeTab = ref<'units' | 'wrong'>('units')
  const loading = ref(false)
  const wrongLoading = ref(false)
  const error = ref('')
  const levelAnalytics = ref<AdminLevelAnalyticsItem[]>([])
  const wrongQuestionStats = ref<AdminWrongQuestionItem[]>([])
  const units = ref<UnitOut[]>([])
  const selectedUnitName = ref('')
  const selectedLevelKey = ref<string | null>(null)
  const wrongKeyword = ref('')
  const selectedWrongQuestionId = ref<number | null>(null)

  const levelOptions = computed(() => units.value.flatMap(unit => {
    if (!Array.isArray(unit.levels)) return []
    return unit.levels.map((level: LevelOut) => ({
      key: `${unit.name}-${level.name}`,
      unitName: unit.name,
      levelName: level.name,
      label: `${unit.name} / ${level.name}`,
    }))
  }))

  const filteredLevelAnalytics = computed(() => (
    selectedUnitName.value
      ? levelAnalytics.value.filter(row => row.unit_name === selectedUnitName.value)
      : levelAnalytics.value
  ))

  const selectedLevelAnalytics = computed(() => (
    levelAnalytics.value.find(row => `${row.unit_name}-${row.level_name}` === selectedLevelKey.value) ?? null
  ))

  const unitSummaryRows = computed(() => {
    const bucket = new Map<string, { attempts: number; students: number; totalAccuracy: number; totalTime: number; count: number }>()
    for (const row of levelAnalytics.value) {
      const current = bucket.get(row.unit_name) ?? { attempts: 0, students: 0, totalAccuracy: 0, totalTime: 0, count: 0 }
      current.attempts += row.total_attempts
      current.students += row.student_count
      current.totalAccuracy += row.correct_rate
      current.totalTime += row.avg_time_spent
      current.count += 1
      bucket.set(row.unit_name, current)
    }
    return Array.from(bucket.entries()).map(([unitName, value]) => ({
      unitName,
      avgAccuracy: value.totalAccuracy / value.count,
      avgTime: value.totalTime / value.count,
      attempts: value.attempts,
      students: value.students,
      levelCount: value.count,
    })).sort((a, b) => a.avgAccuracy - b.avgAccuracy)
  })

  const riskUnits = computed(() => unitSummaryRows.value.slice(0, 5))

  const analyticsKpis = computed(() => {
    const rowCount = levelAnalytics.value.length
    const attempts = levelAnalytics.value.reduce((sum, row) => sum + row.total_attempts, 0)
    const avgAccuracy = rowCount
      ? levelAnalytics.value.reduce((sum, row) => sum + row.correct_rate, 0) / rowCount
      : 0
    const avgTime = rowCount
      ? levelAnalytics.value.reduce((sum, row) => sum + row.avg_time_spent, 0) / rowCount
      : 0
    return [
      { label: '分析关卡', value: formatNumber(rowCount), hint: `${formatNumber(unitSummaryRows.value.length)} 个单元` },
      { label: '累计作答', value: formatNumber(attempts), hint: '关卡明细合计' },
      { label: '平均正确率', value: formatPercent(avgAccuracy), hint: '按关卡平均' },
      { label: '平均耗时', value: formatSeconds(avgTime), hint: '按关卡平均' },
    ]
  })

  const filteredWrongQuestionStats = computed(() => {
    const keyword = wrongKeyword.value.trim().toLowerCase()
    if (!keyword) return wrongQuestionStats.value
    return wrongQuestionStats.value.filter(row => (
      row.question_content.toLowerCase().includes(keyword)
      || row.unit_name.toLowerCase().includes(keyword)
      || row.level_name.toLowerCase().includes(keyword)
    ))
  })

  const highFrequencyWrongQuestions = computed(() => (
    [...wrongQuestionStats.value]
      .sort((a, b) => b.wrong_count - a.wrong_count)
      .slice(0, 5)
  ))

  const selectedWrongQuestion = computed(() => (
    wrongQuestionStats.value.find(row => row.question_id === selectedWrongQuestionId.value) ?? null
  ))

  const wrongKpis = computed(() => {
    const totalWrong = wrongQuestionStats.value.reduce((sum, row) => sum + row.wrong_count, 0)
    const avgWrongRate = wrongQuestionStats.value.length
      ? wrongQuestionStats.value.reduce((sum, row) => sum + row.wrong_rate, 0) / wrongQuestionStats.value.length
      : 0
    return [
      { label: '错题数量', value: formatNumber(wrongQuestionStats.value.length), hint: '统计样本数' },
      { label: '累计错误', value: formatNumber(totalWrong), hint: '错误次数合计' },
      { label: '平均错误率', value: formatPercent(avgWrongRate), hint: '按题目平均' },
    ]
  })

  async function ensureUnitsLoaded() {
    if (units.value.length > 0) return
    const token = readAdminToken()
    if (!token) throw new Error('请先登录教师管理后台。')
    units.value = await fetchUnits(token)
  }

  async function loadLevelAnalytics() {
    const token = readAdminToken()
    if (!token) {
      error.value = '请先登录教师管理后台。'
      levelAnalytics.value = []
      selectedLevelKey.value = null
      return
    }

    loading.value = true
    error.value = ''
    try {
      await ensureUnitsLoaded()
      levelAnalytics.value = await fetchLevelAnalytics(token)
      if (!levelAnalytics.value.some(item => `${item.unit_name}-${item.level_name}` === selectedLevelKey.value)) {
        selectedLevelKey.value = levelAnalytics.value.length
          ? `${levelAnalytics.value[0].unit_name}-${levelAnalytics.value[0].level_name}`
          : null
      }
    } catch (err) {
      error.value = getErrorMessage(err)
    } finally {
      loading.value = false
    }
  }

  async function loadWrongQuestionStats() {
    const token = readAdminToken()
    if (!token) {
      error.value = '请先登录教师管理后台。'
      wrongQuestionStats.value = []
      selectedWrongQuestionId.value = null
      return
    }

    wrongLoading.value = true
    error.value = ''
    try {
      wrongQuestionStats.value = await fetchWrongQuestionStats(token)
      if (!wrongQuestionStats.value.some(item => item.question_id === selectedWrongQuestionId.value)) {
        selectedWrongQuestionId.value = wrongQuestionStats.value[0]?.question_id ?? null
      }
    } catch (err) {
      error.value = getErrorMessage(err)
    } finally {
      wrongLoading.value = false
    }
  }

  async function refreshAll() {
    await Promise.all([loadLevelAnalytics(), loadWrongQuestionStats()])
  }

  return {
    activeTab,
    loading,
    wrongLoading,
    error,
    levelAnalytics,
    wrongQuestionStats,
    units,
    levelOptions,
    selectedUnitName,
    selectedLevelKey,
    wrongKeyword,
    selectedWrongQuestionId,
    filteredLevelAnalytics,
    selectedLevelAnalytics,
    unitSummaryRows,
    riskUnits,
    analyticsKpis,
    filteredWrongQuestionStats,
    highFrequencyWrongQuestions,
    selectedWrongQuestion,
    wrongKpis,
    formatNumber,
    formatPercent,
    formatSeconds,
    loadLevelAnalytics,
    loadWrongQuestionStats,
    refreshAll,
  }
})

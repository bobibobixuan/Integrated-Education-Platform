<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import AdminShell from '@/components/AdminShell.vue'
import AdminBarList from '@/components/admin/AdminBarList.vue'
import AdminMiniLineChart from '@/components/admin/AdminMiniLineChart.vue'
import BrandLogo from '@/components/BrandLogo.vue'
import { changePassword, getMe, login } from '@/api/auth'
import {
  createPvpRoom,
  createQuestion,
  createStudent,
  disableStudent,
  fetchDashboard,
  fetchLevelAnalytics,
  fetchPvpRooms,
  fetchQuestions,
  fetchStudentDetail,
  fetchStudents,
  fetchWrongQuestionStats,
  getRegistrationSetting,
  importQuestions,
  importQuestionsExcel,
  importStudents,
  startPvpRoom,
  finishPvpRoom,
  toggleQuestion,
  updatePvpRoom,
  updateQuestion,
  updateRegistrationSetting,
  updateStudent,
} from '@/api/admin'
import { fetchLeaderboard } from '@/api/leaderboard'
import { fetchUnits } from '@/api/game'
import type {
  AdminDashboardOut,
  AdminLevelAnalyticsItem,
  AdminPvpRoomCreate,
  AdminQuestion,
  AdminStudent,
  AdminStudentDetail,
  AdminWrongQuestionItem,
  LeaderboardEntry,
  LevelOut,
  PvpRoom,
  UnitOut,
  UserResponse,
} from '@/types/api'
import { ADMIN_ENGLISH_NAME, ADMIN_NAME } from '@/brand'

const ADMIN_TOKEN_KEY = 'admin_token'
const LEGACY_ADMIN_TOKEN_KEY = 'admin_jwt_token'
const ADMIN_USER_KEY = 'admin_user'

type AdminTab = 'dashboard' | 'students' | 'leaderboard' | 'analytics' | 'wrong' | 'questions' | 'pvp' | 'import'
type BannerTone = 'success' | 'error'
type ConfirmTone = 'danger' | 'primary'

const tabLabels: Record<AdminTab, string> = {
  dashboard: '仪表盘',
  students: '学生管理',
  leaderboard: '排行榜',
  analytics: '教学分析',
  wrong: '错题统计',
  questions: '题库管理',
  pvp: 'PVP 管理',
  import: '导入中心',
}

const tabDescriptions: Record<AdminTab, string> = {
  dashboard: '先看总体数据，再进入学生、题库和竞技管理。',
  students: '按搜索、排序和状态筛选学生，并查看详细学习表现。',
  leaderboard: '查看战力榜和周活跃榜，快速锁定高表现学生。',
  analytics: '从趋势和单元层面检查教学难点、速度和完成度。',
  wrong: '聚焦高错误题目，定位需要修订或重点讲解的内容。',
  questions: '统一维护题目、关卡归属、知识点说明和启停状态。',
  pvp: '创建、编辑和控制竞技房间，查看成员和对战日志。',
  import: '按任务流程完成 JSON 与 Excel 题库导入。',
}

const tabs = Object.entries(tabLabels).map(([key, label]) => ({ key, label })) as Array<{ key: AdminTab; label: string }>

const activeTab = ref<AdminTab>('dashboard')
const restoring = ref(false)
const loading = ref(false)

const initialSession = readStoredAdminSession()
const adminToken = ref<string | null>(initialSession.token)
const adminUser = ref<UserResponse | null>(initialSession.user)

const banner = ref<{ tone: BannerTone; message: string } | null>(null)
const confirmDialog = ref<{ title: string; message: string; confirmLabel: string; tone: ConfirmTone } | null>(null)
let confirmAction: (() => Promise<void>) | null = null

const loginForm = ref({ username: '', password: '' })
const passwordForm = ref({ old_password: '', new_password: '' })
const passwordMsg = ref('')
const changingPassword = ref(false)
const showPasswordForm = ref(false)

const dashboard = ref<AdminDashboardOut | null>(null)
const allowSelfRegister = ref(false)

const students = ref<AdminStudent[]>([])
const studentsTotal = ref(0)
const studentsPage = ref(1)
const studentsSearch = ref('')
const studentsSortBy = ref<'total_score' | 'accuracy' | 'total_questions'>('total_score')
const studentsOrder = ref<'desc' | 'asc'>('desc')
const studentsIncludeDisabled = ref(false)
const selectedStudentId = ref<number | null>(null)
const studentDetail = ref<AdminStudentDetail | null>(null)
const studentDetailLoading = ref(false)

const leaderboardType = ref<'power' | 'weekly'>('power')
const leaderboardRows = ref<LeaderboardEntry[]>([])
const selectedLeaderboardUserId = ref<number | null>(null)

const levelAnalytics = ref<AdminLevelAnalyticsItem[]>([])
const selectedAnalyticsKey = ref<string | null>(null)

const wrongStats = ref<AdminWrongQuestionItem[]>([])
const selectedWrongQuestionId = ref<number | null>(null)

const questions = ref<AdminQuestion[]>([])
const questionsTotal = ref(0)
const questionsPage = ref(1)
const qFilterSearch = ref('')
const qFilterUnitId = ref(0)
const qFilterType = ref('')
const qIncludeInactive = ref(false)
const selectedQuestionId = ref<number | null>(null)

const units = ref<UnitOut[]>([])

const showQuestionForm = ref(false)
const editingQuestionId = ref<number | null>(null)
const questionForm = ref(createEmptyQuestionForm())

const showStudentForm = ref(false)
const studentForm = ref({ username: '', nickname: '', password: '' })
const showStudentEditForm = ref(false)
const editingStudentId = ref<number | null>(null)
const studentEditForm = ref({ nickname: '', new_password: '' })
const showStudentImportForm = ref(false)
const studentImportText = ref('[\n  {"username": "", "nickname": "", "password": ""}\n]')

const pvpRooms = ref<PvpRoom[]>([])
const selectedRoomId = ref<number | null>(null)
const showPvpForm = ref(false)
const editingPvpRoomId = ref<number | null>(null)
const pvpForm = ref(createEmptyPvpForm())
const pvpSelectableStudents = ref<AdminStudent[]>([])
const pvpSelectorLoading = ref(false)
const pvpStudentFilter = ref('')
const pvpUnitFilter = ref('')
const showFinishedRooms = ref(false)
const adminPvpSocket = ref<WebSocket | null>(null)
const adminPvpSocketReady = ref(false)
let adminPvpReconnectTimer: ReturnType<typeof setTimeout> | null = null
let adminPvpReconnectAttempts = 0

const groupedPvpRooms = computed(() => ({
  waiting: pvpRooms.value.filter(r => r.status === 'waiting' || r.status === 'countdown'),
  running: pvpRooms.value.filter(r => r.status === 'running'),
  finished: pvpRooms.value.filter(r => r.status === 'finished'),
}))

const importText = ref('{\n  "version": "1.0",\n  "unit": "",\n  "questions": []\n}')
const importExcelFile = ref<File | null>(null)
const importExcelUnit = ref('')
const importExcelFileName = ref('')

const pageTitle = computed(() => tabLabels[activeTab.value])
const pageDescription = computed(() => tabDescriptions[activeTab.value])
const toolbarBusy = computed(() => loading.value || changingPassword.value)
const hasAdminSession = computed(() => Boolean(adminToken.value && adminUser.value))
const adminDisplayName = computed(() => adminUser.value?.nickname || adminUser.value?.username || '管理员')
const adminForcePasswordChange = computed(() => Boolean(adminUser.value?.force_password_change))

const levelOptions = computed(() => units.value.flatMap(unit => {
  if (!Array.isArray(unit.levels)) return []
  return unit.levels.map((level: LevelOut) => ({
    levelId: level.id,
    label: `${unit.name} / ${level.name}`,
  }))
}))

const selectedStudent = computed(() => students.value.find(item => item.user_id === selectedStudentId.value) ?? null)
const selectedLeaderboardEntry = computed(() => leaderboardRows.value.find(item => item.user_id === selectedLeaderboardUserId.value) ?? null)
const selectedQuestion = computed(() => questions.value.find(item => item.id === selectedQuestionId.value) ?? null)
const selectedRoom = computed(() => pvpRooms.value.find(item => item.id === selectedRoomId.value) ?? null)
const selectedWrongQuestion = computed(() => wrongStats.value.find(item => item.question_id === selectedWrongQuestionId.value) ?? null)

const dashboardTrendPoints = computed(() => (
  dashboard.value?.hourly_trend.map(item => ({ label: item.date, value: item.count })) ?? []
))

const dashboardKpis = computed(() => {
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

const dashboardQuickActions = computed(() => {
  const questionCount = dashboard.value?.question_count ?? questionsTotal.value
  const studentCount = studentsTotal.value > 0 ? studentsTotal.value : (dashboard.value?.user_count ?? 0)
  return [
    { key: 'students' as AdminTab, title: '学生管理', desc: '查看详情、修改昵称、重置密码和批量导入。', meta: `${formatNumber(studentCount)} 人` },
    { key: 'questions' as AdminTab, title: '题库管理', desc: '按单元、类型和状态筛题，直接编辑题干与知识点。', meta: `${formatNumber(questionCount)} 题` },
    { key: 'pvp' as AdminTab, title: '竞技管理', desc: '创建房间、分配题量和控制比赛开始与结算。', meta: `${formatNumber(pvpRooms.value.length)} 间` },
    { key: 'import' as AdminTab, title: '导入中心', desc: '用 JSON 或 Excel 快速扩充题库。', meta: '两种导入方式' },
  ]
})

const unitAccuracyBars = computed(() => (
  dashboard.value?.unit_accuracy.map(unit => ({
    label: unit.unit_name,
    value: Math.round(unit.accuracy),
    hint: `${formatPercent(unit.accuracy)} 正确率`,
    tone: 'blue' as const,
  })) ?? []
))

const weakestUnitBars = computed(() => (
  dashboard.value?.weakest_units.map(unit => ({
    label: unit.unit_name,
    value: Math.round(unit.wrong_rate ?? 0),
    hint: `${formatPercent(unit.accuracy)} 正确率 / ${formatSeconds(unit.avg_time_spent)} 平均耗时`,
    tone: 'amber' as const,
  })) ?? []
))

const topStudentBars = computed(() => (
  dashboard.value?.top_students.map(student => ({
    label: student.nickname,
    value: student.power_score ?? 0,
    hint: `${formatPercent(student.accuracy)} 正确率 / ${formatNumber(student.total_questions)} 题`,
    tone: 'green' as const,
  })) ?? []
))

const analyticsUnitBars = computed(() => {
  const bucket = new Map<string, { attempts: number; totalAccuracy: number; totalTime: number; count: number }>()
  for (const row of levelAnalytics.value) {
    const current = bucket.get(row.unit_name) ?? { attempts: 0, totalAccuracy: 0, totalTime: 0, count: 0 }
    current.attempts += row.total_attempts
    current.totalAccuracy += row.correct_rate
    current.totalTime += row.avg_time_spent
    current.count += 1
    bucket.set(row.unit_name, current)
  }
  return Array.from(bucket.entries()).map(([unitName, value]) => ({
    label: unitName,
    value: Math.round(value.totalAccuracy / value.count),
    hint: `${formatSeconds(value.totalTime / value.count)} 平均耗时 / ${formatNumber(value.attempts)} 次作答`,
    tone: 'blue' as const,
  })).sort((a, b) => b.value - a.value)
})

const analyticsTimeBars = computed(() => {
  const bucket = new Map<string, { totalTime: number; count: number }>()
  for (const row of levelAnalytics.value) {
    const current = bucket.get(row.unit_name) ?? { totalTime: 0, count: 0 }
    current.totalTime += row.avg_time_spent
    current.count += 1
    bucket.set(row.unit_name, current)
  }
  return Array.from(bucket.entries()).map(([unitName, value]) => ({
    label: unitName,
    value: Math.round(value.totalTime / value.count),
    hint: '单元平均耗时',
    tone: 'amber' as const,
  })).sort((a, b) => b.value - a.value)
})

const wrongQuestionBars = computed(() => (
  wrongStats.value.slice(0, 8).map(row => ({
    label: `${row.unit_name} / ${row.level_name}`,
    value: Math.round(row.wrong_rate),
    hint: `${formatNumber(row.wrong_count)} 次错误 / ${formatNumber(row.total_attempts)} 次作答`,
    tone: 'red' as const,
  }))
))

function createEmptyQuestionForm() {
  return {
    content: '',
    type: '选择题',
    answer: '',
    options: [
      { letter: 'A', text: '' },
      { letter: 'B', text: '' },
      { letter: 'C', text: '' },
      { letter: 'D', text: '' },
    ],
    level_id: 0,
    title: '',
    knowledge_meaning: '',
    knowledge_rule: '',
    knowledge_error: '',
    knowledge_example: '',
  }
}

function createEmptyPvpForm() {
  return {
    title: '',
    description: '',
    group_size: 6,
    member_user_ids: [] as number[],
    question_unit_ids: [] as number[],
    question_count: 10,
    battle_time_limit_seconds: 300,
  }
}

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
  ensureAdminPvpSocket()
}

function clearAdminSession() {
  closeAdminPvpSocket()
  adminToken.value = null
  adminUser.value = null
  localStorage.removeItem(ADMIN_TOKEN_KEY)
  localStorage.removeItem(LEGACY_ADMIN_TOKEN_KEY)
  localStorage.removeItem(ADMIN_USER_KEY)
}

function clearBanner() {
  banner.value = null
}

function showSuccess(message: string) {
  banner.value = { tone: 'success', message }
}

function showError(message: string) {
  banner.value = { tone: 'error', message }
}

function getErrorMessage(error: unknown) {
  return error instanceof Error ? error.message : '操作失败，请稍后重试。'
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

function roomStatusLabel(status: string) {
  if (status === 'waiting') return '待开始'
  if (status === 'running') return '进行中'
  if (status === 'finished') return '已结束'
  return status
}

function roomStatusTone(status: string) {
  if (status === 'running') return 'ok'
  if (status === 'finished') return 'neutral'
  return 'warn'
}

function selectedStudentAccuracy() {
  if (!studentDetail.value || studentDetail.value.total_questions === 0) return '0%'
  return formatPercent((studentDetail.value.total_correct / studentDetail.value.total_questions) * 100)
}

function askConfirm(meta: { title: string; message: string; confirmLabel: string; tone: ConfirmTone }, action: () => Promise<void>) {
  confirmDialog.value = meta
  confirmAction = action
}

async function submitConfirmAction() {
  if (!confirmAction) return
  const action = confirmAction
  confirmDialog.value = null
  confirmAction = null
  await action()
}

async function restoreAdminSession() {
  if (!adminToken.value) return
  restoring.value = true
  try {
    const me = await getMe(adminToken.value)
    if (me.role !== 'admin') {
      clearAdminSession()
      return
    }
    persistAdminSession(adminToken.value, me)
    await loadTab('dashboard')
  } catch {
    clearAdminSession()
  } finally {
    restoring.value = false
  }
}

async function handleAdminLogin() {
  clearBanner()
  loading.value = true
  try {
    const tokenRes = await login(loginForm.value)
    const me = await getMe(tokenRes.access_token)
    if (me.role !== 'admin') {
      throw new Error('该账号不是管理员。')
    }
    persistAdminSession(tokenRes.access_token, me)
    loginForm.value.password = ''
    showSuccess('登录成功，已进入教师管理后台。')
    await loadTab('dashboard')
  } catch (error: unknown) {
    showError(getErrorMessage(error))
  } finally {
    loading.value = false
  }
}

function handleAdminLogout() {
  clearAdminSession()
  banner.value = null
  activeTab.value = 'dashboard'
}

function openPasswordForm() {
  passwordMsg.value = ''
  passwordForm.value = { old_password: '', new_password: '' }
  showPasswordForm.value = true
}

async function handleChangePassword() {
  if (!adminToken.value) return
  changingPassword.value = true
  passwordMsg.value = ''
  try {
    const tokenRes = await changePassword(adminToken.value, passwordForm.value)
    const me = await getMe(tokenRes.access_token)
    persistAdminSession(tokenRes.access_token, me)
    passwordMsg.value = '密码已修改。'
    showSuccess('管理员密码已更新。')
    passwordForm.value = { old_password: '', new_password: '' }
    if (!me.force_password_change) {
      showPasswordForm.value = false
    }
  } catch (error: unknown) {
    passwordMsg.value = getErrorMessage(error)
  } finally {
    changingPassword.value = false
  }
}

async function ensureUnitsLoaded() {
  if (!adminToken.value || units.value.length > 0) return
  units.value = await fetchUnits(adminToken.value)
}

async function loadDashboardData() {
  if (!adminToken.value) return
  const token = adminToken.value
  const [dashboardRes, registrationRes] = await Promise.all([
    fetchDashboard(token),
    getRegistrationSetting(token),
  ])
  dashboard.value = dashboardRes
  allowSelfRegister.value = registrationRes.allow_self_register
}

async function openStudentDetail(userId: number) {
  if (!adminToken.value) return
  selectedStudentId.value = userId
  studentDetailLoading.value = true
  try {
    studentDetail.value = await fetchStudentDetail(adminToken.value, userId)
  } catch (error: unknown) {
    showError(getErrorMessage(error))
  } finally {
    studentDetailLoading.value = false
  }
}

async function loadStudentsData() {
  if (!adminToken.value) return
  const token = adminToken.value
  const res = await fetchStudents(
    token,
    studentsPage.value,
    20,
    studentsSearch.value,
    studentsSortBy.value,
    studentsOrder.value,
    studentsIncludeDisabled.value,
  )
  students.value = res.items
  studentsTotal.value = res.total
  const currentSelected = selectedStudentId.value && res.items.some(item => item.user_id === selectedStudentId.value)
  if (res.items.length === 0) {
    selectedStudentId.value = null
    studentDetail.value = null
    return
  }
  if (!currentSelected) {
    await openStudentDetail(res.items[0].user_id)
    return
  }
  if (selectedStudentId.value !== null) {
    await openStudentDetail(selectedStudentId.value)
  }
}

async function loadLeaderboardData() {
  if (!adminToken.value) return
  const res = await fetchLeaderboard(adminToken.value, leaderboardType.value, 50)
  leaderboardRows.value = res.entries
  if (!leaderboardRows.value.some(item => item.user_id === selectedLeaderboardUserId.value)) {
    selectedLeaderboardUserId.value = leaderboardRows.value[0]?.user_id ?? null
  }
}

async function loadAnalyticsData() {
  if (!adminToken.value) return
  levelAnalytics.value = await fetchLevelAnalytics(adminToken.value)
  if (!levelAnalytics.value.some(item => `${item.unit_name}-${item.level_name}` === selectedAnalyticsKey.value)) {
    selectedAnalyticsKey.value = levelAnalytics.value.length
      ? `${levelAnalytics.value[0].unit_name}-${levelAnalytics.value[0].level_name}`
      : null
  }
}

async function loadWrongStatsData() {
  if (!adminToken.value) return
  wrongStats.value = await fetchWrongQuestionStats(adminToken.value)
  if (!wrongStats.value.some(item => item.question_id === selectedWrongQuestionId.value)) {
    selectedWrongQuestionId.value = wrongStats.value[0]?.question_id ?? null
  }
}

async function loadQuestionsData() {
  if (!adminToken.value) return
  const token = adminToken.value
  await ensureUnitsLoaded()
  const unitId = qFilterUnitId.value > 0 ? qFilterUnitId.value : undefined
  const res = await fetchQuestions(
    token,
    questionsPage.value,
    20,
    undefined,
    unitId,
    qFilterType.value,
    qFilterSearch.value,
    qIncludeInactive.value,
  )
  questions.value = res.items
  questionsTotal.value = res.total
  if (!questions.value.some(item => item.id === selectedQuestionId.value)) {
    selectedQuestionId.value = questions.value[0]?.id ?? null
  }
}

async function loadPvpData() {
  if (!adminToken.value) return
  await ensureUnitsLoaded()
  pvpRooms.value = await fetchPvpRooms(adminToken.value)
  if (!pvpRooms.value.some(item => item.id === selectedRoomId.value)) {
    selectedRoomId.value = pvpRooms.value[0]?.id ?? null
  }
}

const filteredPvpStudents = computed(() => {
  const keyword = pvpStudentFilter.value.trim().toLowerCase()
  if (!keyword) return pvpSelectableStudents.value
  return pvpSelectableStudents.value.filter(student => (
    student.nickname.toLowerCase().includes(keyword)
    || student.username.toLowerCase().includes(keyword)
    || String(student.user_id).includes(keyword)
  ))
})

const filteredPvpUnits = computed(() => {
  const keyword = pvpUnitFilter.value.trim().toLowerCase()
  if (!keyword) return units.value
  return units.value.filter(unit => (
    unit.name.toLowerCase().includes(keyword)
    || unit.subtitle.toLowerCase().includes(keyword)
    || String(unit.id).includes(keyword)
  ))
})

const selectedPvpStudents = computed(() => {
  const selectedIds = new Set(pvpForm.value.member_user_ids)
  return pvpSelectableStudents.value.filter(student => selectedIds.has(student.user_id))
})

const selectedPvpUnits = computed(() => {
  const selectedIds = new Set(pvpForm.value.question_unit_ids)
  return units.value.filter(unit => selectedIds.has(unit.id))
})

const pvpStudentSummary = computed(() => {
  const count = selectedPvpStudents.value.length
  if (count === 0) return '请选择学生'
  const names = selectedPvpStudents.value.slice(0, 3).map(student => student.nickname)
  const rest = count - names.length
  return rest > 0 ? `${names.join('、')} 等 ${count} 人` : `${names.join('、')} · 共 ${count} 人`
})

const pvpUnitSummary = computed(() => {
  const count = selectedPvpUnits.value.length
  if (count === 0) return '请选择单元'
  const names = selectedPvpUnits.value.slice(0, 3).map(unit => unit.name)
  const rest = count - names.length
  return rest > 0 ? `${names.join('、')} 等 ${count} 个单元` : `${names.join('、')} · 共 ${count} 个单元`
})

async function loadTab(nextTab: AdminTab) {
  activeTab.value = nextTab
  if (!adminToken.value) return
  if (nextTab === 'pvp') {
    ensureAdminPvpSocket()
    requestAdminPvpRooms()
  }
  loading.value = true
  try {
    if (nextTab === 'dashboard') await loadDashboardData()
    if (nextTab === 'students') await loadStudentsData()
    if (nextTab === 'leaderboard') await loadLeaderboardData()
    if (nextTab === 'analytics') await loadAnalyticsData()
    if (nextTab === 'wrong') await loadWrongStatsData()
    if (nextTab === 'questions') await loadQuestionsData()
    if (nextTab === 'pvp') await loadPvpData()
  } catch (error: unknown) {
    showError(getErrorMessage(error))
  } finally {
    loading.value = false
  }
}

async function refreshActiveTab() {
  await loadTab(activeTab.value)
}

function getAdminWsUrl() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${protocol}//${window.location.host}/ws/online`
}

function clearAdminPvpReconnectTimer() {
  if (!adminPvpReconnectTimer) return
  clearTimeout(adminPvpReconnectTimer)
  adminPvpReconnectTimer = null
}

function requestAdminPvpRooms() {
  if (!adminPvpSocket.value || adminPvpSocket.value.readyState !== WebSocket.OPEN || !adminPvpSocketReady.value) {
    return
  }
  adminPvpSocket.value.send(JSON.stringify({ type: 'request_pvp_rooms' }))
}

function scheduleAdminPvpReconnect() {
  if (!adminToken.value) return
  clearAdminPvpReconnectTimer()
  const delay = Math.min(1000 * Math.pow(2, adminPvpReconnectAttempts), 30000)
  adminPvpReconnectAttempts += 1
  adminPvpReconnectTimer = setTimeout(() => {
    ensureAdminPvpSocket()
  }, delay)
}

function closeAdminPvpSocket() {
  clearAdminPvpReconnectTimer()
  adminPvpReconnectAttempts = 0
  adminPvpSocketReady.value = false
  const current = adminPvpSocket.value
  adminPvpSocket.value = null
  if (!current) return
  current.onopen = null
  current.onmessage = null
  current.onclose = null
  current.onerror = null
  if (current.readyState === WebSocket.OPEN || current.readyState === WebSocket.CONNECTING) {
    current.close(1000, 'admin logout')
  }
}

function ensureAdminPvpSocket() {
  if (!adminToken.value) return
  const current = adminPvpSocket.value
  if (current && (current.readyState === WebSocket.OPEN || current.readyState === WebSocket.CONNECTING)) {
    if (activeTab.value === 'pvp' && adminPvpSocketReady.value) {
      requestAdminPvpRooms()
    }
    return
  }

  clearAdminPvpReconnectTimer()
  adminPvpSocketReady.value = false
  const ws = new WebSocket(getAdminWsUrl())
  adminPvpSocket.value = ws

  ws.onopen = () => {
    adminPvpReconnectAttempts = 0
    ws.send(JSON.stringify({ type: 'auth', token: adminToken.value }))
  }

  ws.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data) as { type?: string; status?: string; rooms?: PvpRoom[] }
      if (msg.type === 'auth_state') {
        adminPvpSocketReady.value = msg.status === 'authenticated'
        if (adminPvpSocketReady.value && activeTab.value === 'pvp') {
          requestAdminPvpRooms()
        }
        return
      }
      if (msg.type === 'pvp_rooms' && Array.isArray(msg.rooms)) {
        pvpRooms.value = msg.rooms
        if (!pvpRooms.value.some(item => item.id === selectedRoomId.value)) {
          selectedRoomId.value = pvpRooms.value[0]?.id ?? null
        }
      }
    } catch {
      // ignore malformed messages
    }
  }

  ws.onclose = (event) => {
    if (adminPvpSocket.value === ws) {
      adminPvpSocket.value = null
      adminPvpSocketReady.value = false
    }
    if (event.code !== 1000) {
      scheduleAdminPvpReconnect()
    }
  }

  ws.onerror = () => {
    // onclose will handle reconnect
  }
}

// Auto-refresh dashboard every 30s
let dashboardPollTimer: ReturnType<typeof setInterval> | null = null
watch(activeTab, (tab) => {
  if (dashboardPollTimer) { clearInterval(dashboardPollTimer); dashboardPollTimer = null }
  if (tab === 'dashboard') {
    dashboardPollTimer = setInterval(() => loadDashboardData(), 30_000)
  }
  if (tab === 'pvp') {
    ensureAdminPvpSocket()
    requestAdminPvpRooms()
  }
})
onUnmounted(() => {
  if (dashboardPollTimer) clearInterval(dashboardPollTimer)
  closeAdminPvpSocket()
})

async function toggleRegistration() {
  if (!adminToken.value) return
  try {
    const res = await updateRegistrationSetting(adminToken.value, allowSelfRegister.value)
    allowSelfRegister.value = res.allow_self_register
    showSuccess(`学生自主注册已${allowSelfRegister.value ? '开启' : '关闭'}。`)
  } catch (error: unknown) {
    showError(getErrorMessage(error))
  }
}

async function saveStudent() {
  if (!adminToken.value) return
  loading.value = true
  try {
    await createStudent(adminToken.value, studentForm.value)
    showStudentForm.value = false
    studentForm.value = { username: '', nickname: '', password: '' }
    showSuccess('学生账号已创建。')
    await loadStudentsData()
  } catch (error: unknown) {
    showError(getErrorMessage(error))
  } finally {
    loading.value = false
  }
}

function openEditStudentForm(student: AdminStudent) {
  editingStudentId.value = student.user_id
  studentEditForm.value = { nickname: student.nickname, new_password: '' }
  showStudentEditForm.value = true
}

async function saveStudentEdit() {
  if (!adminToken.value || editingStudentId.value === null) return
  loading.value = true
  try {
    const body: Record<string, unknown> = {}
    if (studentEditForm.value.nickname.trim()) body.nickname = studentEditForm.value.nickname.trim()
    if (studentEditForm.value.new_password.trim()) body.new_password = studentEditForm.value.new_password.trim()
    await updateStudent(adminToken.value, editingStudentId.value, body)
    showStudentEditForm.value = false
    showSuccess('学生信息已更新。')
    await loadStudentsData()
  } catch (error: unknown) {
    showError(getErrorMessage(error))
  } finally {
    loading.value = false
  }
}

async function saveStudentImport() {
  if (!adminToken.value) return
  loading.value = true
  try {
    const payload = JSON.parse(studentImportText.value) as Array<{ username: string; nickname: string; password: string }>
    const res = await importStudents(adminToken.value, { students: payload })
    showStudentImportForm.value = false
    showSuccess(`${res.created} 个学生账号已导入。`)
    await loadStudentsData()
  } catch (error: unknown) {
    showError(getErrorMessage(error))
  } finally {
    loading.value = false
  }
}

function resetPvpSelectorFilters() {
  pvpStudentFilter.value = ''
  pvpUnitFilter.value = ''
}

function togglePvpSelection(field: 'member_user_ids' | 'question_unit_ids', value: number, checked: boolean) {
  const current = field === 'member_user_ids'
    ? pvpForm.value.member_user_ids
    : pvpForm.value.question_unit_ids
  const next = checked
    ? Array.from(new Set([...current, value]))
    : current.filter(item => item !== value)
  if (field === 'member_user_ids') {
    pvpForm.value.member_user_ids = next
  } else {
    pvpForm.value.question_unit_ids = next
  }
}

function handlePvpCheckboxChange(field: 'member_user_ids' | 'question_unit_ids', value: number, event: Event) {
  togglePvpSelection(field, value, (event.currentTarget as HTMLInputElement).checked)
}

function selectAllVisiblePvpStudents() {
  pvpForm.value.member_user_ids = Array.from(new Set([
    ...pvpForm.value.member_user_ids,
    ...filteredPvpStudents.value.map(student => student.user_id),
  ]))
}

function clearPvpStudents() {
  pvpForm.value.member_user_ids = []
}

function selectAllVisiblePvpUnits() {
  pvpForm.value.question_unit_ids = Array.from(new Set([
    ...pvpForm.value.question_unit_ids,
    ...filteredPvpUnits.value.map(unit => unit.id),
  ]))
}

function clearPvpUnits() {
  pvpForm.value.question_unit_ids = []
}

function unitLevelCount(unit: UnitOut) {
  if (Array.isArray(unit.levels)) return unit.levels.length
  return typeof unit.levels === 'number' ? unit.levels : 0
}

async function loadPvpFormOptions() {
  if (!adminToken.value) return
  pvpSelectorLoading.value = true
  try {
    await ensureUnitsLoaded()
    const allStudents: AdminStudent[] = []
    let page = 1
    const pageSize = 100
    while (true) {
      const res = await fetchStudents(
        adminToken.value,
        page,
        pageSize,
        '',
        'total_score',
        'desc',
        true,
      )
      allStudents.push(...res.items)
      if (allStudents.length >= res.total || res.items.length < pageSize) break
      page += 1
    }
    pvpSelectableStudents.value = allStudents
      .slice()
      .sort((a, b) => a.nickname.localeCompare(b.nickname, 'zh-CN', { numeric: true }))
  } catch (error: unknown) {
    showError(getErrorMessage(error))
  } finally {
    pvpSelectorLoading.value = false
  }
}

function confirmDisableStudent(userId: number) {
  askConfirm(
    {
      title: '禁用学生账号',
      message: '该学生将无法继续登录，历史成绩会被保留。确认继续吗？',
      confirmLabel: '确认禁用',
      tone: 'danger',
    },
    async () => {
      if (!adminToken.value) return
      loading.value = true
      try {
        await disableStudent(adminToken.value, userId)
        showSuccess('学生账号已禁用。')
        await loadStudentsData()
      } catch (error: unknown) {
        showError(getErrorMessage(error))
      } finally {
        loading.value = false
      }
    },
  )
}

function buildPvpRoomPayload(): AdminPvpRoomCreate {
  return {
    title: pvpForm.value.title.trim(),
    description: pvpForm.value.description.trim(),
    group_size: pvpForm.value.group_size,
    member_user_ids: [...pvpForm.value.member_user_ids],
    question_unit_ids: [...pvpForm.value.question_unit_ids],
    question_count: pvpForm.value.question_count,
    battle_time_limit_seconds: pvpForm.value.battle_time_limit_seconds,
  }
}

async function openNewPvpForm() {
  editingPvpRoomId.value = null
  pvpForm.value = createEmptyPvpForm()
  resetPvpSelectorFilters()
  showPvpForm.value = true
  await loadPvpFormOptions()
}

async function openEditPvpForm(room: PvpRoom) {
  editingPvpRoomId.value = room.id
  pvpForm.value = {
    title: room.title,
    description: room.description || '',
    group_size: room.group_size,
    member_user_ids: room.members.map(member => member.user_id),
    question_unit_ids: [...room.question_unit_ids],
    question_count: room.question_count,
    battle_time_limit_seconds: room.battle_time_limit_seconds,
  }
  resetPvpSelectorFilters()
  showPvpForm.value = true
  await loadPvpFormOptions()
}

async function savePvpRoom() {
  if (!adminToken.value) return
  loading.value = true
  try {
    if (editingPvpRoomId.value !== null) {
      await updatePvpRoom(adminToken.value, editingPvpRoomId.value, buildPvpRoomPayload())
      showSuccess('竞技房间已更新。')
    } else {
      await createPvpRoom(adminToken.value, buildPvpRoomPayload())
      showSuccess('竞技房间已创建。')
    }
    showPvpForm.value = false
    await loadPvpData()
  } catch (error: unknown) {
    showError(getErrorMessage(error))
  } finally {
    loading.value = false
  }
}

function confirmStartPvpRoom(roomId: number) {
  askConfirm(
    {
      title: '开始竞技房间',
      message: '开始后学生将进入正式对战流程，确认立即开始吗？',
      confirmLabel: '立即开始',
      tone: 'primary',
    },
    async () => {
      if (!adminToken.value) return
      loading.value = true
      try {
        await startPvpRoom(adminToken.value, roomId)
        showSuccess('竞技房间已开始。')
        await loadPvpData()
      } catch (error: unknown) {
        showError(getErrorMessage(error))
      } finally {
        loading.value = false
      }
    },
  )
}

function confirmFinishPvpRoom(roomId: number) {
  askConfirm(
    {
      title: '结束竞技房间',
      message: '结束后将立即进行结算并锁定当前结果，确认继续吗？',
      confirmLabel: '结束并结算',
      tone: 'danger',
    },
    async () => {
      if (!adminToken.value) return
      loading.value = true
      try {
        await finishPvpRoom(adminToken.value, roomId)
        showSuccess('竞技房间已结束。')
        await loadPvpData()
      } catch (error: unknown) {
        showError(getErrorMessage(error))
      } finally {
        loading.value = false
      }
    },
  )
}

async function submitQuestionImport() {
  if (!adminToken.value) return
  loading.value = true
  try {
    const payload = JSON.parse(importText.value) as Record<string, unknown>
    const res = await importQuestions(adminToken.value, payload)
    showSuccess(res.message || 'JSON 题库已导入。')
    await loadTab('questions')
  } catch (error: unknown) {
    showError(getErrorMessage(error))
  } finally {
    loading.value = false
  }
}

function handleImportFile(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  file.text().then(text => {
    importText.value = text
  }).catch(() => {
    showError('读取导入文件失败。')
  })
}

function handleExcelFile(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  importExcelFile.value = file
  importExcelFileName.value = file.name
  if (!importExcelUnit.value) {
    importExcelUnit.value = file.name.replace(/\.(xlsx|xlsm)$/i, '')
  }
}

async function submitExcelImport() {
  if (!adminToken.value || !importExcelFile.value) return
  if (!importExcelUnit.value.trim()) {
    showError('请先填写目标单元名称。')
    return
  }
  loading.value = true
  try {
    const res = await importQuestionsExcel(adminToken.value, importExcelFile.value, importExcelUnit.value.trim())
    importExcelFile.value = null
    importExcelFileName.value = ''
    importExcelUnit.value = ''
    const input = document.getElementById('excel-file-input') as HTMLInputElement | null
    if (input) input.value = ''
    showSuccess(res.message || 'Excel 题库已导入。')
    await loadTab('questions')
  } catch (error: unknown) {
    showError(getErrorMessage(error))
  } finally {
    loading.value = false
  }
}

function openNewQuestionForm() {
  editingQuestionId.value = null
  questionForm.value = createEmptyQuestionForm()
  questionForm.value.level_id = levelOptions.value[0]?.levelId ?? 0
  showQuestionForm.value = true
}

function openEditQuestionForm(question: AdminQuestion) {
  editingQuestionId.value = question.id
  questionForm.value = {
    content: question.content,
    type: question.type,
    answer: question.answer,
    options: question.options ?? [
      { letter: 'A', text: '' },
      { letter: 'B', text: '' },
      { letter: 'C', text: '' },
      { letter: 'D', text: '' },
    ],
    level_id: question.level_id,
    title: question.title || '',
    knowledge_meaning: question.knowledge_meaning || '',
    knowledge_rule: question.knowledge_rule || '',
    knowledge_error: question.knowledge_error || '',
    knowledge_example: question.knowledge_example || '',
  }
  showQuestionForm.value = true
}

async function saveQuestion() {
  if (!adminToken.value) return
  loading.value = true
  try {
    const payload = {
      content: questionForm.value.content,
      type: questionForm.value.type,
      answer: questionForm.value.answer,
      options: questionForm.value.options.filter(item => item.text.trim()),
      level_id: questionForm.value.level_id,
      title: questionForm.value.title.trim() || questionForm.value.content.slice(0, 60),
      knowledge_meaning: questionForm.value.knowledge_meaning.trim(),
      knowledge_rule: questionForm.value.knowledge_rule.trim(),
      knowledge_error: questionForm.value.knowledge_error.trim(),
      knowledge_example: questionForm.value.knowledge_example.trim(),
    }
    if (editingQuestionId.value !== null) {
      await updateQuestion(adminToken.value, editingQuestionId.value, payload)
      showSuccess('题目已更新。')
    } else {
      await createQuestion(adminToken.value, payload)
      showSuccess('题目已创建。')
    }
    showQuestionForm.value = false
    await loadQuestionsData()
  } catch (error: unknown) {
    showError(getErrorMessage(error))
  } finally {
    loading.value = false
  }
}

function confirmToggleQuestion(questionId: number, isActive: boolean) {
  askConfirm(
    {
      title: isActive ? '禁用题目' : '启用题目',
      message: isActive ? '禁用后该题目不会继续出现在学生端。' : '启用后该题目会重新参与出题。',
      confirmLabel: isActive ? '确认禁用' : '确认启用',
      tone: isActive ? 'danger' : 'primary',
    },
    async () => {
      if (!adminToken.value) return
      loading.value = true
      try {
        await toggleQuestion(adminToken.value, questionId, !isActive)
        showSuccess(`题目已${isActive ? '禁用' : '启用'}。`)
        await loadQuestionsData()
      } catch (error: unknown) {
        showError(getErrorMessage(error))
      } finally {
        loading.value = false
      }
    },
  )
}

onMounted(restoreAdminSession)
</script>

<template>
  <div v-if="!hasAdminSession" class="admin-login-page" data-theme="admin">
    <section class="admin-login-card surface-card surface-card--strong">
      <div class="admin-login-card__meta">
        <BrandLogo size="lg" :alt="ADMIN_NAME" />
        <div>
          <span class="admin-login-card__eyebrow">{{ ADMIN_ENGLISH_NAME }}</span>
          <strong>{{ ADMIN_NAME }}</strong>
          <p>数据总览、学生管理、题库维护和 PVP 控制都在这里完成。</p>
        </div>
      </div>

      <div v-if="banner" class="feedback-banner" :class="`is-${banner.tone}`" role="alert">
        <span>{{ banner.message }}</span>
        <button type="button" class="inline-clear" @click="clearBanner">关闭</button>
      </div>

      <div v-if="restoring" class="loading-copy">恢复会话中...</div>

      <form v-else class="auth-form admin-login-form" @submit.prevent="handleAdminLogin">
        <div class="field-stack">
          <label for="admin-username">用户名</label>
          <input id="admin-username" v-model.trim="loginForm.username" type="text" autocomplete="username" />
        </div>
        <div class="field-stack">
          <label for="admin-password">密码</label>
          <input id="admin-password" v-model="loginForm.password" type="password" autocomplete="current-password" />
        </div>
        <button type="submit" class="primary-button admin-login-form__submit" :disabled="loading">
          {{ loading ? '登录中...' : '进入管理后台' }}
        </button>
      </form>
    </section>
  </div>

  <AdminShell
    v-else
    :title="pageTitle"
    :user-name="adminDisplayName"
    :active-tab="activeTab"
    :tabs="tabs"
    @select="value => loadTab(value as AdminTab)"
    @logout="handleAdminLogout"
  >
    <template #toolbar>
      <button type="button" class="ghost-button" :disabled="toolbarBusy" @click="refreshActiveTab">刷新当前页</button>
      <button type="button" class="ghost-button" @click="openPasswordForm">修改密码</button>
    </template>

    <section class="page-intro surface-card surface-card--strong">
      <div>
        <span class="page-intro__eyebrow">Overview</span>
        <h2>{{ pageTitle }}</h2>
        <p>{{ pageDescription }}</p>
      </div>
      <div class="page-intro__meta">
        <span class="status-chip status-chip--neutral">管理员 {{ adminDisplayName }}</span>
        <span v-if="loading" class="status-chip status-chip--warn">数据刷新中</span>
      </div>
    </section>

    <div v-if="banner" class="feedback-banner" :class="`is-${banner.tone}`" role="alert">
      <span>{{ banner.message }}</span>
      <button type="button" class="inline-clear" @click="clearBanner">关闭</button>
    </div>

    <section v-if="adminForcePasswordChange" class="surface-card surface-card--strong admin-urgent-panel">
      <div>
        <h3>首次登录需要先修改密码</h3>
        <p>为避免共享默认密码带来的风险，请先设置新的管理员密码。</p>
      </div>
      <div class="admin-urgent-panel__actions">
        <div class="field-stack">
          <label for="force-password">新密码</label>
          <input id="force-password" v-model="passwordForm.new_password" type="password" />
        </div>
        <p v-if="passwordMsg" class="password-msg" :class="{ 'msg-error': passwordMsg !== '密码已修改。' }">{{ passwordMsg }}</p>
        <button type="button" class="primary-button" :disabled="changingPassword" @click="handleChangePassword">
          {{ changingPassword ? '处理中...' : '更新密码' }}
        </button>
      </div>
    </section>

    <template v-if="activeTab === 'dashboard'">
      <section class="surface-card surface-card--strong admin-workspace-card">
        <div class="workspace-head">
          <div>
            <h3>核心指标</h3>
            <p>首屏优先展示老师每天最常看的六个指标。</p>
          </div>
          <label class="toggle-control">
            <span>允许学生自主注册</span>
            <input v-model="allowSelfRegister" type="checkbox" @change="toggleRegistration" />
          </label>
        </div>
        <div class="admin-kpi-grid">
          <article v-for="metric in dashboardKpis" :key="metric.label" class="admin-kpi-card">
            <span class="admin-kpi-card__label">{{ metric.label }}</span>
            <strong class="admin-kpi-card__value mono-number">{{ metric.value }}</strong>
            <span class="admin-kpi-card__hint">{{ metric.hint }}</span>
          </article>
        </div>
      </section>

      <section class="dashboard-layout">
        <div class="dashboard-layout__main">
          <article class="surface-card surface-card--strong admin-workspace-card">
            <div class="workspace-head">
              <div>
                <h3>近 1 小时作答趋势</h3>
                <p>用折线概览每天的答题热度变化。</p>
              </div>
              <span class="status-chip status-chip--neutral">7 天</span>
            </div>
            <AdminMiniLineChart :points="dashboardTrendPoints" aria-label="近 7 天作答趋势图" />
          </article>

          <div class="dashboard-chart-grid">
            <article class="surface-card surface-card--strong admin-workspace-card">
              <div class="workspace-head">
                <div>
                  <h3>单元正确率对比</h3>
                  <p>快速识别基础稳固和薄弱的单元。</p>
                </div>
              </div>
              <AdminBarList :items="unitAccuracyBars" suffix="%" empty-copy="暂无单元正确率数据" />
            </article>

            <article class="surface-card surface-card--strong admin-workspace-card">
              <div class="workspace-head">
                <div>
                  <h3>重点风险单元</h3>
                  <p>按错误率和耗时筛出优先干预对象。</p>
                </div>
              </div>
              <AdminBarList :items="weakestUnitBars" suffix="%" empty-copy="暂无风险单元数据" />
            </article>
          </div>
        </div>

        <aside class="dashboard-layout__side">
          <article class="surface-card surface-card--strong admin-workspace-card">
            <div class="workspace-head">
              <div>
                <h3>快捷入口</h3>
                <p>常用模块直接跳转，不再从长页面里找入口。</p>
              </div>
            </div>
            <div class="quick-action-list">
              <button
                v-for="action in dashboardQuickActions"
                :key="action.key"
                type="button"
                class="quick-action-card"
                @click="loadTab(action.key)"
              >
                <div>
                  <strong>{{ action.title }}</strong>
                  <p>{{ action.desc }}</p>
                </div>
                <span class="quick-action-card__meta">{{ action.meta }}</span>
              </button>
            </div>
          </article>

          <article class="surface-card surface-card--strong admin-workspace-card">
            <div class="workspace-head">
              <div>
                <h3>重点学生</h3>
                <p>当前战力领先学生与近期未活跃学生。</p>
              </div>
            </div>
            <AdminBarList :items="topStudentBars" empty-copy="暂无重点学生数据" />
            <div class="alert-list">
              <article
                v-for="student in dashboard?.inactive_students ?? []"
                :key="student.user_id"
                class="alert-list__item"
              >
                <div>
                  <strong>{{ student.nickname }}</strong>
                  <span>{{ student.total_questions || 0 }} 题 / 最近 {{ formatDateTime(student.last_active) }}</span>
                </div>
                <button type="button" class="ghost-button" @click="loadTab('students').then(() => openStudentDetail(student.user_id))">查看</button>
              </article>
            </div>
          </article>
        </aside>
      </section>
    </template>

    <template v-if="activeTab === 'students'">
      <section class="workspace-layout">
        <article class="surface-card surface-card--strong admin-workspace-card workspace-card-main">
          <div class="workspace-head">
            <div>
              <h3>学生列表</h3>
              <p>搜索、排序和状态筛选统一放在同一条工具栏里。</p>
            </div>
            <div class="toolbar-group">
              <button type="button" class="secondary-button" @click="showStudentImportForm = true">批量导入</button>
              <button type="button" class="primary-button" @click="showStudentForm = true">新增学生</button>
            </div>
          </div>

          <div class="admin-filter-bar">
            <div class="field-stack">
              <label for="student-search">搜索学生</label>
              <input id="student-search" v-model.trim="studentsSearch" type="text" placeholder="用户名或昵称" @keyup.enter="studentsPage = 1; loadStudentsData()" />
            </div>
            <div class="field-stack">
              <label for="student-sort">排序依据</label>
              <select id="student-sort" v-model="studentsSortBy" @change="studentsPage = 1; loadStudentsData()">
                <option value="total_score">总分</option>
                <option value="accuracy">正确率</option>
                <option value="total_questions">作答量</option>
              </select>
            </div>
            <div class="field-stack">
              <label for="student-order">排序方向</label>
              <select id="student-order" v-model="studentsOrder" @change="studentsPage = 1; loadStudentsData()">
                <option value="desc">从高到低</option>
                <option value="asc">从低到高</option>
              </select>
            </div>
            <label class="toggle-control toggle-control--inline">
              <span>包含已禁用</span>
              <input v-model="studentsIncludeDisabled" type="checkbox" @change="studentsPage = 1; loadStudentsData()" />
            </label>
          </div>

          <div class="table-scroll">
            <table class="app-table admin-table">
              <thead>
                <tr>
                  <th>学生</th>
                  <th>总分</th>
                  <th>战力</th>
                  <th>正确率</th>
                  <th>作答量</th>
                  <th>最近活跃</th>
                  <th>状态</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="student in students"
                  :key="student.user_id"
                  :class="{ 'is-selected': student.user_id === selectedStudentId }"
                  @click="openStudentDetail(student.user_id)"
                >
                  <td>
                    <div class="table-title-cell">
                      <strong>{{ student.nickname }}</strong>
                      <span>@{{ student.username }}</span>
                    </div>
                  </td>
                  <td class="mono-number">{{ formatNumber(student.total_score) }}</td>
                  <td class="mono-number">{{ formatNumber(student.power_score) }}</td>
                  <td>{{ formatPercent(student.accuracy) }}</td>
                  <td>{{ formatNumber(student.total_questions) }}</td>
                  <td>{{ formatDateTime(student.last_active) }}</td>
                  <td>
                    <span class="status-chip" :class="student.is_active ? 'status-chip--ok' : 'status-chip--neutral'">
                      {{ student.is_active ? '正常' : '已禁用' }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="workspace-footer">
            <span class="pill">共 {{ formatNumber(studentsTotal) }} 位学生</span>
            <div class="toolbar-group">
              <button type="button" class="ghost-button" :disabled="studentsPage <= 1" @click="studentsPage -= 1; loadStudentsData()">上一页</button>
              <button type="button" class="ghost-button" :disabled="studentsPage * 20 >= studentsTotal" @click="studentsPage += 1; loadStudentsData()">下一页</button>
            </div>
          </div>
        </article>

        <aside class="workspace-side-column">
          <article class="surface-card surface-card--strong admin-workspace-card workspace-side-card">
            <div class="workspace-head">
              <div>
                <h3>学生详情</h3>
                <p v-if="selectedStudent">{{ selectedStudent.nickname }} 的学习状态与关卡表现。</p>
                <p v-else>先从左侧选择一个学生。</p>
              </div>
            </div>

            <div v-if="studentDetailLoading" class="empty-state">加载学生详情中...</div>
            <div v-else-if="studentDetail && selectedStudent" class="detail-stack">
              <div class="detail-profile">
                <div>
                  <strong>{{ studentDetail.nickname }}</strong>
                  <span>@{{ studentDetail.username }}</span>
                </div>
                <span class="status-chip" :class="studentDetail.is_active ? 'status-chip--ok' : 'status-chip--neutral'">
                  {{ studentDetail.is_active ? '正常' : '已禁用' }}
                </span>
              </div>

              <div class="detail-metric-grid">
                <article class="detail-metric-card">
                  <span>总作答</span>
                  <strong class="mono-number">{{ formatNumber(studentDetail.total_questions) }}</strong>
                </article>
                <article class="detail-metric-card">
                  <span>正确率</span>
                  <strong>{{ selectedStudentAccuracy() }}</strong>
                </article>
                <article class="detail-metric-card">
                  <span>总分</span>
                  <strong class="mono-number">{{ formatNumber(studentDetail.total_score) }}</strong>
                </article>
                <article class="detail-metric-card">
                  <span>总战力</span>
                  <strong class="mono-number">{{ formatNumber(studentDetail.power_score) }}</strong>
                </article>
              </div>

              <div class="side-actions">
                <button type="button" class="ghost-button" @click="openEditStudentForm(selectedStudent)">编辑资料</button>
                <button
                  type="button"
                  class="danger-button"
                  :disabled="!selectedStudent.is_active"
                  @click="confirmDisableStudent(selectedStudent.user_id)"
                >
                  禁用账号
                </button>
              </div>

              <div class="detail-section">
                <div class="detail-section__head">
                  <h4>关卡战力拆解</h4>
                  <span>{{ studentDetail.level_breakdown.length }} 项</span>
                </div>
                <div class="record-list compact-scroll">
                  <article v-for="row in studentDetail.level_breakdown" :key="`${row.level_id}-${row.level_name}`" class="record-item">
                    <div class="record-item__q">
                      <strong>{{ row.unit_name }} / {{ row.level_name }}</strong>
                    </div>
                    <div class="record-item__meta">
                      <span>总战力 {{ row.total }}</span>
                      <span>通关 {{ row.clear }}</span>
                      <span>满分 {{ row.perfect }}</span>
                      <span>速度 {{ row.speed }}</span>
                      <span>连击 {{ row.combo }}</span>
                    </div>
                  </article>
                </div>
              </div>
            </div>
            <div v-else class="empty-state">选择学生后会在这里显示个人数据、关卡拆解和快捷操作。</div>
          </article>
        </aside>
      </section>
    </template>

    <template v-if="activeTab === 'leaderboard'">
      <section class="workspace-layout">
        <article class="surface-card surface-card--strong admin-workspace-card workspace-card-main">
          <div class="workspace-head">
            <div>
              <h3>排行榜</h3>
              <p>支持战力榜和周活跃榜两种查看方式。</p>
            </div>
            <div class="toolbar-group">
              <button type="button" class="ghost-button" :class="{ 'toolbar-chip-active': leaderboardType === 'power' }" @click="leaderboardType = 'power'; loadLeaderboardData()">战力榜</button>
              <button type="button" class="ghost-button" :class="{ 'toolbar-chip-active': leaderboardType === 'weekly' }" @click="leaderboardType = 'weekly'; loadLeaderboardData()">周活跃榜</button>
            </div>
          </div>
          <div class="table-scroll">
            <table class="app-table admin-table">
              <thead>
                <tr>
                  <th>排名</th>
                  <th>学生</th>
                  <th>{{ leaderboardType === 'power' ? '战力' : '周活跃' }}</th>
                  <th>正确率</th>
                  <th>通关数</th>
                  <th>星数</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="entry in leaderboardRows"
                  :key="entry.user_id"
                  :class="{ 'is-selected': entry.user_id === selectedLeaderboardUserId }"
                  @click="selectedLeaderboardUserId = entry.user_id"
                >
                  <td class="mono-number">#{{ entry.rank }}</td>
                  <td>{{ entry.nickname }}</td>
                  <td class="mono-number">{{ leaderboardType === 'power' ? formatNumber(entry.power_score) : formatNumber(entry.weekly_activity) }}</td>
                  <td>{{ formatPercent(entry.accuracy) }}</td>
                  <td>{{ formatNumber(entry.completed_levels) }}</td>
                  <td>{{ formatNumber(entry.total_stars) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </article>

        <aside class="workspace-side-column">
          <article class="surface-card surface-card--strong admin-workspace-card workspace-side-card">
            <div class="workspace-head">
              <div>
                <h3>当前选中</h3>
                <p v-if="selectedLeaderboardEntry">聚焦当前排名学生的主要指标。</p>
                <p v-else>从左侧选择一名学生查看。</p>
              </div>
            </div>
            <div v-if="selectedLeaderboardEntry" class="detail-stack">
              <div class="detail-profile">
                <div>
                  <strong>{{ selectedLeaderboardEntry.nickname }}</strong>
                  <span>排名 #{{ selectedLeaderboardEntry.rank }}</span>
                </div>
              </div>
              <div class="detail-metric-grid">
                <article class="detail-metric-card">
                  <span>战力</span>
                  <strong class="mono-number">{{ formatNumber(selectedLeaderboardEntry.power_score) }}</strong>
                </article>
                <article class="detail-metric-card">
                  <span>正确率</span>
                  <strong>{{ formatPercent(selectedLeaderboardEntry.accuracy) }}</strong>
                </article>
                <article class="detail-metric-card">
                  <span>通关数</span>
                  <strong class="mono-number">{{ formatNumber(selectedLeaderboardEntry.completed_levels) }}</strong>
                </article>
                <article class="detail-metric-card">
                  <span>总星数</span>
                  <strong class="mono-number">{{ formatNumber(selectedLeaderboardEntry.total_stars) }}</strong>
                </article>
              </div>
            </div>
            <div v-else class="empty-state">当前榜单还没有数据。</div>
          </article>
        </aside>
      </section>
    </template>

    <template v-if="activeTab === 'analytics'">
      <section class="surface-card surface-card--strong admin-workspace-card">
        <div class="workspace-head">
          <div>
            <h3>教学分析概览</h3>
            <p>按单元聚合正确率和平均耗时，方便先看结构性问题。</p>
          </div>
        </div>
        <div class="dashboard-chart-grid">
          <article class="admin-subcard">
            <div class="workspace-head workspace-head--compact">
              <div>
                <h4>单元正确率</h4>
              </div>
            </div>
            <AdminBarList :items="analyticsUnitBars" suffix="%" empty-copy="暂无分析数据" />
          </article>
          <article class="admin-subcard">
            <div class="workspace-head workspace-head--compact">
              <div>
                <h4>单元平均耗时</h4>
              </div>
            </div>
            <AdminBarList :items="analyticsTimeBars" suffix="s" empty-copy="暂无耗时数据" />
          </article>
        </div>
      </section>

      <section class="workspace-layout">
        <article class="surface-card surface-card--strong admin-workspace-card workspace-card-main">
          <div class="workspace-head">
            <div>
              <h3>关卡明细</h3>
              <p>双列图表下方保留完整明细表，便于横向比对。</p>
            </div>
          </div>
          <div class="table-scroll">
            <table class="app-table admin-table">
              <thead>
                <tr>
                  <th>单元</th>
                  <th>关卡</th>
                  <th>参与人数</th>
                  <th>作答次数</th>
                  <th>正确率</th>
                  <th>平均耗时</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="row in levelAnalytics"
                  :key="`${row.unit_name}-${row.level_name}`"
                  :class="{ 'is-selected': `${row.unit_name}-${row.level_name}` === selectedAnalyticsKey }"
                  @click="selectedAnalyticsKey = `${row.unit_name}-${row.level_name}`"
                >
                  <td>{{ row.unit_name }}</td>
                  <td>{{ row.level_name }}</td>
                  <td>{{ formatNumber(row.student_count) }}</td>
                  <td>{{ formatNumber(row.total_attempts) }}</td>
                  <td>{{ formatPercent(row.correct_rate) }}</td>
                  <td>{{ formatSeconds(row.avg_time_spent) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </article>

        <aside class="workspace-side-column">
          <article class="surface-card surface-card--strong admin-workspace-card workspace-side-card">
            <div class="workspace-head">
              <div>
                <h3>当前关卡焦点</h3>
                <p>被选中的关卡会在这里显示关键数据。</p>
              </div>
            </div>
            <div v-if="selectedAnalyticsKey" class="detail-stack">
              <template v-for="row in levelAnalytics.filter(item => `${item.unit_name}-${item.level_name}` === selectedAnalyticsKey)" :key="selectedAnalyticsKey">
                <div class="detail-profile">
                  <div>
                    <strong>{{ row.level_name }}</strong>
                    <span>{{ row.unit_name }}</span>
                  </div>
                </div>
                <div class="detail-metric-grid">
                  <article class="detail-metric-card">
                    <span>参与人数</span>
                    <strong class="mono-number">{{ formatNumber(row.student_count) }}</strong>
                  </article>
                  <article class="detail-metric-card">
                    <span>作答次数</span>
                    <strong class="mono-number">{{ formatNumber(row.total_attempts) }}</strong>
                  </article>
                  <article class="detail-metric-card">
                    <span>正确率</span>
                    <strong>{{ formatPercent(row.correct_rate) }}</strong>
                  </article>
                  <article class="detail-metric-card">
                    <span>平均耗时</span>
                    <strong>{{ formatSeconds(row.avg_time_spent) }}</strong>
                  </article>
                </div>
              </template>
            </div>
            <div v-else class="empty-state">选择一个关卡后再查看详细分析。</div>
          </article>
        </aside>
      </section>
    </template>

    <template v-if="activeTab === 'wrong'">
      <section class="surface-card surface-card--strong admin-workspace-card">
        <div class="workspace-head">
          <div>
            <h3>高错误题目总览</h3>
            <p>先看错误率最高的题目，再到下方表格核对具体内容。</p>
          </div>
        </div>
        <AdminBarList :items="wrongQuestionBars" suffix="%" empty-copy="暂无错题统计数据" />
      </section>

      <section class="workspace-layout">
        <article class="surface-card surface-card--strong admin-workspace-card workspace-card-main">
          <div class="workspace-head">
            <div>
              <h3>错题明细</h3>
              <p>错误率、错误次数和总作答量分开呈现，方便判断是真难还是样本少。</p>
            </div>
          </div>
          <div class="table-scroll">
            <table class="app-table admin-table">
              <thead>
                <tr>
                  <th>题目</th>
                  <th>单元</th>
                  <th>关卡</th>
                  <th>错误次数</th>
                  <th>错误率</th>
                  <th>总作答</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="row in wrongStats"
                  :key="row.question_id"
                  :class="{ 'is-selected': row.question_id === selectedWrongQuestionId }"
                  @click="selectedWrongQuestionId = row.question_id"
                >
                  <td class="question-content">{{ row.question_content }}</td>
                  <td>{{ row.unit_name }}</td>
                  <td>{{ row.level_name }}</td>
                  <td>{{ formatNumber(row.wrong_count) }}</td>
                  <td>{{ formatPercent(row.wrong_rate) }}</td>
                  <td>{{ formatNumber(row.total_attempts) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </article>

        <aside class="workspace-side-column">
          <article class="surface-card surface-card--strong admin-workspace-card workspace-side-card">
            <div class="workspace-head">
              <div>
                <h3>当前错题</h3>
                <p v-if="selectedWrongQuestion">查看题目内容和错误规模。</p>
                <p v-else>从左侧选择一题。</p>
              </div>
            </div>
            <div v-if="selectedWrongQuestion" class="detail-stack">
              <div class="detail-section">
                <h4>题目内容</h4>
                <p class="question-preview">{{ selectedWrongQuestion.question_content }}</p>
              </div>
              <div class="detail-metric-grid">
                <article class="detail-metric-card">
                  <span>错误次数</span>
                  <strong class="mono-number">{{ formatNumber(selectedWrongQuestion.wrong_count) }}</strong>
                </article>
                <article class="detail-metric-card">
                  <span>错误率</span>
                  <strong>{{ formatPercent(selectedWrongQuestion.wrong_rate) }}</strong>
                </article>
                <article class="detail-metric-card">
                  <span>总作答</span>
                  <strong class="mono-number">{{ formatNumber(selectedWrongQuestion.total_attempts) }}</strong>
                </article>
              </div>
            </div>
            <div v-else class="empty-state">当前没有可查看的错题。</div>
          </article>
        </aside>
      </section>
    </template>

    <template v-if="activeTab === 'questions'">
      <section class="workspace-layout">
        <article class="surface-card surface-card--strong admin-workspace-card workspace-card-main">
          <div class="workspace-head">
            <div>
              <h3>题库列表</h3>
              <p>统一用工具栏筛选、右侧详情查看、弹窗完成编辑。</p>
            </div>
            <button type="button" class="primary-button" @click="openNewQuestionForm">新建题目</button>
          </div>

          <div class="admin-filter-bar admin-filter-bar--wide">
            <div class="field-stack">
              <label for="question-search">搜索题目</label>
              <input id="question-search" v-model.trim="qFilterSearch" type="text" placeholder="按题干搜索" @keyup.enter="questionsPage = 1; loadQuestionsData()" />
            </div>
            <div class="field-stack">
              <label for="question-unit">单元</label>
              <select id="question-unit" v-model.number="qFilterUnitId" @change="questionsPage = 1; loadQuestionsData()">
                <option :value="0">全部单元</option>
                <option v-for="unit in units" :key="unit.id" :value="unit.id">{{ unit.name }}</option>
              </select>
            </div>
            <div class="field-stack">
              <label for="question-type">题型</label>
              <select id="question-type" v-model="qFilterType" @change="questionsPage = 1; loadQuestionsData()">
                <option value="">全部题型</option>
                <option value="选择题">选择题</option>
                <option value="多选题">多选题</option>
                <option value="判断题">判断题</option>
                <option value="填空题">填空题</option>
              </select>
            </div>
            <label class="toggle-control toggle-control--inline">
              <span>包含停用题</span>
              <input v-model="qIncludeInactive" type="checkbox" @change="questionsPage = 1; loadQuestionsData()" />
            </label>
          </div>

          <div class="table-scroll">
            <table class="app-table admin-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>题目</th>
                  <th>题型</th>
                  <th>单元</th>
                  <th>关卡</th>
                  <th>状态</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="question in questions"
                  :key="question.id"
                  :class="{ 'is-selected': question.id === selectedQuestionId }"
                  @click="selectedQuestionId = question.id"
                >
                  <td class="mono-number">#{{ question.id }}</td>
                  <td class="question-content">{{ question.content }}</td>
                  <td>{{ question.type }}</td>
                  <td>{{ question.unit_name }}</td>
                  <td>{{ question.level_name }}</td>
                  <td>
                    <span class="status-chip" :class="question.is_active ? 'status-chip--ok' : 'status-chip--neutral'">
                      {{ question.is_active ? '启用' : '停用' }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="workspace-footer">
            <span class="pill">共 {{ formatNumber(questionsTotal) }} 题</span>
            <div class="toolbar-group">
              <button type="button" class="ghost-button" :disabled="questionsPage <= 1" @click="questionsPage -= 1; loadQuestionsData()">上一页</button>
              <button type="button" class="ghost-button" :disabled="questionsPage * 20 >= questionsTotal" @click="questionsPage += 1; loadQuestionsData()">下一页</button>
            </div>
          </div>
        </article>

        <aside class="workspace-side-column">
          <article class="surface-card surface-card--strong admin-workspace-card workspace-side-card">
            <div class="workspace-head">
              <div>
                <h3>题目详情</h3>
                <p v-if="selectedQuestion">查看答案、知识点说明和快捷操作。</p>
                <p v-else>从左侧列表选择一题。</p>
              </div>
            </div>

            <div v-if="selectedQuestion" class="detail-stack">
              <div class="detail-section">
                <h4>{{ selectedQuestion.title || '未命名题目' }}</h4>
                <p class="question-preview">{{ selectedQuestion.content }}</p>
              </div>
              <div v-if="selectedQuestion.options?.length" class="option-list">
                <article v-for="option in selectedQuestion.options" :key="option.letter" class="option-list__item">
                  <strong>{{ option.letter }}</strong>
                  <span>{{ option.text }}</span>
                </article>
              </div>
              <div class="detail-metric-grid">
                <article class="detail-metric-card">
                  <span>正确答案</span>
                  <strong>{{ selectedQuestion.answer }}</strong>
                </article>
                <article class="detail-metric-card">
                  <span>单元 / 关卡</span>
                  <strong>{{ selectedQuestion.unit_name }} / {{ selectedQuestion.level_name }}</strong>
                </article>
              </div>
              <div class="detail-section">
                <h4>知识点说明</h4>
                <div class="knowledge-stack">
                  <p><strong>含义：</strong>{{ selectedQuestion.knowledge_meaning || '未填写' }}</p>
                  <p><strong>规则：</strong>{{ selectedQuestion.knowledge_rule || '未填写' }}</p>
                  <p><strong>易错点：</strong>{{ selectedQuestion.knowledge_error || '未填写' }}</p>
                  <p><strong>示例：</strong>{{ selectedQuestion.knowledge_example || '未填写' }}</p>
                </div>
              </div>
              <div class="side-actions">
                <button type="button" class="ghost-button" @click="openEditQuestionForm(selectedQuestion)">编辑题目</button>
                <button type="button" class="danger-button" @click="confirmToggleQuestion(selectedQuestion.id, selectedQuestion.is_active)">
                  {{ selectedQuestion.is_active ? '禁用题目' : '启用题目' }}
                </button>
              </div>
            </div>
            <div v-else class="empty-state">选择题目后会在这里显示完整内容和知识点。</div>
          </article>
        </aside>
      </section>
    </template>

    <template v-if="activeTab === 'pvp'">
      <section class="workspace-layout">
        <article class="surface-card surface-card--strong admin-workspace-card workspace-card-main">
          <div class="workspace-head">
            <div>
              <h3>竞技房间列表</h3>
              <p>房间状态、成员数和题量统一放在主列表，操作收口到右侧。</p>
            </div>
            <button type="button" class="primary-button" @click="openNewPvpForm">新建房间</button>
          </div>

          <div v-if="pvpRooms.length === 0" class="empty-state">当前还没有竞技房间。</div>
          <div v-else class="room-list">
            <!-- 未开始 -->
            <details class="room-group" open>
              <summary class="room-group__head">
                <span>未开始</span>
                <span class="pill">{{ groupedPvpRooms.waiting.length }}</span>
              </summary>
              <button
                v-for="room in groupedPvpRooms.waiting"
                :key="room.id"
                type="button"
                class="room-list__item"
                :class="{ 'is-selected': room.id === selectedRoomId }"
                @click="selectedRoomId = room.id"
              >
                <div class="room-list__head">
                  <div>
                    <strong>{{ room.title }}</strong>
                    <span>{{ room.description || '未填写房间说明' }}</span>
                  </div>
                  <span class="status-chip" :class="`status-chip--${roomStatusTone(room.status)}`">
                    {{ roomStatusLabel(room.status) }}
                  </span>
                </div>
                <div class="room-list__meta">
                  <span>成员 {{ room.member_count }}/{{ room.group_size }}</span>
                  <span>题量 {{ room.question_count }}</span>
                </div>
              </button>
              <div v-if="groupedPvpRooms.waiting.length === 0" class="room-group__empty">暂无未开始房间</div>
            </details>

            <!-- 正在对战 -->
            <details class="room-group" open>
              <summary class="room-group__head">
                <span>正在对战</span>
                <span class="pill">{{ groupedPvpRooms.running.length }}</span>
              </summary>
              <button
                v-for="room in groupedPvpRooms.running"
                :key="room.id"
                type="button"
                class="room-list__item"
                :class="{ 'is-selected': room.id === selectedRoomId }"
                @click="selectedRoomId = room.id"
              >
                <div class="room-list__head">
                  <div>
                    <strong>{{ room.title }}</strong>
                    <span>{{ room.description || '未填写房间说明' }}</span>
                  </div>
                  <span class="status-chip status-chip--ok">进行中</span>
                </div>
                <div class="room-list__meta">
                  <span>成员 {{ room.member_count }}/{{ room.group_size }}</span>
                  <span>题量 {{ room.question_count }}</span>
                </div>
              </button>
              <div v-if="groupedPvpRooms.running.length === 0" class="room-group__empty">暂无进行中房间</div>
            </details>

            <!-- 已完成 -->
            <details class="room-group" :open="showFinishedRooms" @toggle="showFinishedRooms = ($event.target as HTMLDetailsElement).open">
              <summary class="room-group__head room-group__head--finished">
                <span>已完成</span>
                <span class="pill">{{ groupedPvpRooms.finished.length }}</span>
              </summary>
              <button
                v-for="room in groupedPvpRooms.finished"
                :key="room.id"
                type="button"
                class="room-list__item"
                :class="{ 'is-selected': room.id === selectedRoomId }"
                @click="selectedRoomId = room.id"
              >
                <div class="room-list__head">
                  <div>
                    <strong>{{ room.title }}</strong>
                    <span>{{ room.description || '未填写房间说明' }}</span>
                  </div>
                  <span class="status-chip status-chip--neutral">已结束</span>
                </div>
                <div class="room-list__meta">
                  <span>成员 {{ room.member_count }}/{{ room.group_size }}</span>
                  <span>题量 {{ room.question_count }}</span>
                </div>
              </button>
              <div v-if="groupedPvpRooms.finished.length === 0" class="room-group__empty">暂无已结束房间</div>
            </details>
          </div>
        </article>

        <aside class="workspace-side-column">
          <article class="surface-card surface-card--strong admin-workspace-card workspace-side-card">
            <div class="workspace-head">
              <div>
                <h3>房间详情</h3>
                <p v-if="selectedRoom">从这里管理当前房间、成员和日志。</p>
                <p v-else>从左侧选择一个房间。</p>
              </div>
            </div>
            <div v-if="selectedRoom" class="detail-stack">
              <div class="detail-profile">
                <div>
                  <strong>{{ selectedRoom.title }}</strong>
                  <span>{{ roomStatusLabel(selectedRoom.status) }}</span>
                </div>
                <span class="status-chip" :class="`status-chip--${roomStatusTone(selectedRoom.status)}`">{{ roomStatusLabel(selectedRoom.status) }}</span>
              </div>

              <div class="detail-metric-grid">
                <article class="detail-metric-card">
                  <span>成员</span>
                  <strong class="mono-number">{{ selectedRoom.member_count }}/{{ selectedRoom.group_size }}</strong>
                </article>
                <article class="detail-metric-card">
                  <span>题量</span>
                  <strong class="mono-number">{{ selectedRoom.question_count }}</strong>
                </article>
                <article class="detail-metric-card">
                  <span>总时限</span>
                  <strong>{{ formatSeconds(selectedRoom.battle_time_limit_seconds) }}</strong>
                </article>
                <article class="detail-metric-card">
                  <span>已准备</span>
                  <strong class="mono-number">{{ formatNumber(selectedRoom.ready_count) }}</strong>
                </article>
              </div>

              <div class="side-actions">
                <button type="button" class="ghost-button" @click="openEditPvpForm(selectedRoom)">编辑房间</button>
                <button
                  v-if="selectedRoom.status === 'waiting'"
                  type="button"
                  class="secondary-button"
                  @click="confirmStartPvpRoom(selectedRoom.id)"
                >
                  开始比赛
                </button>
                <button
                  v-if="selectedRoom.status === 'running'"
                  type="button"
                  class="danger-button"
                  @click="confirmFinishPvpRoom(selectedRoom.id)"
                >
                  结束并结算
                </button>
              </div>

              <div class="detail-section">
                <div class="detail-section__head">
                  <h4>{{ selectedRoom.status === 'finished' ? '本场排名' : '房间成员' }}</h4>
                  <span>{{ selectedRoom.members.length }} 人</span>
                </div>
                <div class="record-list compact-scroll">
                  <article v-for="member in selectedRoom.members" :key="member.user_id" class="record-item" :class="{ 'record-item--podium': selectedRoom.status === 'finished' && member.rank <= 3 }">
                    <div class="record-item__q">
                      <strong>
                        <span v-if="selectedRoom.status === 'finished' && member.rank <= 3" class="admin-rank-badge">TOP{{ member.rank }}</span>
                        #{{ member.rank }} {{ member.nickname }}
                      </strong>
                    </div>
                    <div class="record-item__meta">
                      <span>战力 {{ member.battle_power }}</span>
                      <span>答对 {{ member.correct_count }}</span>
                      <span v-if="selectedRoom.status !== 'finished'">答错 {{ member.wrong_count }}</span>
                      <span v-if="selectedRoom.status === 'finished'">正确率 {{ member.accuracy }}%</span>
                      <span v-if="selectedRoom.status !== 'finished'">{{ member.is_ready ? '已准备' : '未准备' }}</span>
                    </div>
                  </article>
                </div>
              </div>

              <div class="detail-section">
                <div class="detail-section__head">
                  <h4>房间日志</h4>
                  <span>{{ selectedRoom.logs.length }} 条</span>
                </div>
                <div class="record-list compact-scroll">
                  <article v-for="log in selectedRoom.logs" :key="log.id" class="record-item">
                    <div class="record-item__q">{{ log.message }}</div>
                    <div class="record-item__meta">
                      <span>{{ log.category }}</span>
                      <span>{{ formatDateTime(log.created_at) }}</span>
                    </div>
                  </article>
                </div>
              </div>
            </div>
            <div v-else class="empty-state">选择房间后会在这里展示控制按钮、成员和日志。</div>
          </article>
        </aside>
      </section>
    </template>

    <template v-if="activeTab === 'import'">
      <section class="surface-card surface-card--strong admin-workspace-card">
        <div class="workspace-head">
          <div>
            <h3>导入流程</h3>
            <p>导入页面单独按任务流程组织，不混入普通管理列表。</p>
          </div>
        </div>
        <div class="import-flow">
          <article class="import-step-card">
            <span class="import-step-card__index">01</span>
            <div>
              <strong>选择导入方式</strong>
              <p>JSON 适合结构化迁移，Excel 适合老师按模板维护题目。</p>
            </div>
          </article>
          <article class="import-step-card">
            <span class="import-step-card__index">02</span>
            <div>
              <strong>检查目标单元</strong>
              <p>Excel 导入会按你填写的单元名进行分组落库。</p>
            </div>
          </article>
          <article class="import-step-card">
            <span class="import-step-card__index">03</span>
            <div>
              <strong>完成导入并回到题库</strong>
              <p>成功后会自动跳回题库管理，继续核查题目状态。</p>
            </div>
          </article>
        </div>
      </section>

      <div class="dashboard-chart-grid">
        <article class="surface-card surface-card--strong admin-workspace-card">
          <div class="workspace-head">
            <div>
              <h3>JSON 导入</h3>
              <p>支持直接上传 `.json` 文件，也支持粘贴原始文本。</p>
            </div>
          </div>
          <div class="import-drop-zone">
            <input type="file" accept=".json" @change="handleImportFile" />
            <span>选择 JSON 文件并自动填充到下方文本框</span>
          </div>
          <div class="field-stack">
            <label for="json-import-text">导入内容</label>
            <textarea id="json-import-text" v-model="importText" rows="16" />
          </div>
          <button type="button" class="primary-button" :disabled="loading" @click="submitQuestionImport">
            {{ loading ? '导入中...' : '执行 JSON 导入' }}
          </button>
        </article>

        <article class="surface-card surface-card--strong admin-workspace-card">
          <div class="workspace-head">
            <div>
              <h3>Excel 导入</h3>
              <p>支持 `.xlsx` / `.xlsm` 文件，适合老师从模板直接维护题目。</p>
            </div>
          </div>
          <div class="form-grid">
            <div class="field-stack">
              <label for="excel-unit">目标单元名称</label>
              <input id="excel-unit" v-model="importExcelUnit" type="text" placeholder="例如：程序设计概述" />
            </div>
            <div class="field-stack">
              <label for="excel-file-input">选择 Excel 文件</label>
              <input id="excel-file-input" type="file" accept=".xlsx,.xlsm" @change="handleExcelFile" />
            </div>
          </div>
          <p class="import-file-hint">{{ importExcelFileName ? `已选择：${importExcelFileName}` : '尚未选择文件' }}</p>
          <button type="button" class="primary-button" :disabled="loading || !importExcelFile" @click="submitExcelImport">
            {{ loading ? '导入中...' : '执行 Excel 导入' }}
          </button>
        </article>
      </div>
    </template>

    <div v-if="showQuestionForm" class="overlay" @click.self="showQuestionForm = false">
      <div class="modal surface-card surface-card--strong">
        <div class="workspace-head">
          <div>
            <h3>{{ editingQuestionId !== null ? '编辑题目' : '新建题目' }}</h3>
            <p>题目内容、答案和知识点说明统一在这一个表单里维护。</p>
          </div>
          <button type="button" class="inline-clear" @click="showQuestionForm = false">关闭</button>
        </div>
        <div class="form-grid">
          <div class="field-stack form-grid__full">
            <label for="question-title">标题</label>
            <input id="question-title" v-model="questionForm.title" type="text" placeholder="不填则自动从题干截取" />
          </div>
          <div class="field-stack form-grid__full">
            <label for="question-content-input">题目内容</label>
            <textarea id="question-content-input" v-model="questionForm.content" rows="4" />
          </div>
          <div class="field-stack">
            <label for="question-type-input">题型</label>
            <select id="question-type-input" v-model="questionForm.type">
              <option value="选择题">选择题</option>
              <option value="多选题">多选题</option>
              <option value="判断题">判断题</option>
              <option value="填空题">填空题</option>
            </select>
          </div>
          <div class="field-stack">
            <label for="question-level-input">所属关卡</label>
            <select id="question-level-input" v-model.number="questionForm.level_id">
              <option v-for="option in levelOptions" :key="option.levelId" :value="option.levelId">{{ option.label }}</option>
            </select>
          </div>
          <div v-if="questionForm.type === '选择题' || questionForm.type === '多选题'" class="form-grid__full">
            <div class="option-grid">
              <div v-for="(option, index) in questionForm.options" :key="option.letter" class="field-stack">
                <label :for="`question-option-${index}`">选项 {{ option.letter }}</label>
                <input :id="`question-option-${index}`" v-model="option.text" type="text" />
              </div>
            </div>
          </div>
          <div class="field-stack">
            <label for="question-answer">正确答案</label>
            <input id="question-answer" v-model="questionForm.answer" type="text" placeholder="如 A / 对 / True" />
          </div>
          <div class="field-stack">
            <label for="question-meaning">知识点含义</label>
            <input id="question-meaning" v-model="questionForm.knowledge_meaning" type="text" />
          </div>
          <div class="field-stack">
            <label for="question-rule">知识点规则</label>
            <input id="question-rule" v-model="questionForm.knowledge_rule" type="text" />
          </div>
          <div class="field-stack">
            <label for="question-error">常见错误</label>
            <input id="question-error" v-model="questionForm.knowledge_error" type="text" />
          </div>
          <div class="field-stack form-grid__full">
            <label for="question-example">示例说明</label>
            <textarea id="question-example" v-model="questionForm.knowledge_example" rows="3" />
          </div>
        </div>
        <div class="modal-actions">
          <button type="button" class="ghost-button" @click="showQuestionForm = false">取消</button>
          <button type="button" class="primary-button" :disabled="loading" @click="saveQuestion">{{ loading ? '保存中...' : '保存题目' }}</button>
        </div>
      </div>
    </div>

    <div v-if="showStudentEditForm" class="overlay" @click.self="showStudentEditForm = false">
      <div class="modal surface-card surface-card--strong">
        <div class="workspace-head">
          <div>
            <h3>编辑学生</h3>
            <p>可修改昵称，也可为学生重置密码。</p>
          </div>
          <button type="button" class="inline-clear" @click="showStudentEditForm = false">关闭</button>
        </div>
        <div class="form-grid">
          <div class="field-stack">
            <label for="edit-student-nickname">昵称</label>
            <input id="edit-student-nickname" v-model="studentEditForm.nickname" type="text" />
          </div>
          <div class="field-stack">
            <label for="edit-student-password">新密码</label>
            <input id="edit-student-password" v-model="studentEditForm.new_password" type="password" placeholder="留空则不修改" />
          </div>
        </div>
        <div class="modal-actions">
          <button type="button" class="ghost-button" @click="showStudentEditForm = false">取消</button>
          <button type="button" class="primary-button" :disabled="loading" @click="saveStudentEdit">{{ loading ? '保存中...' : '保存修改' }}</button>
        </div>
      </div>
    </div>

    <div v-if="showStudentForm" class="overlay" @click.self="showStudentForm = false">
      <div class="modal surface-card surface-card--strong">
        <div class="workspace-head">
          <div>
            <h3>新增学生</h3>
            <p>创建后学生即可用账号密码登录学生端。</p>
          </div>
          <button type="button" class="inline-clear" @click="showStudentForm = false">关闭</button>
        </div>
        <div class="form-grid">
          <div class="field-stack">
            <label for="student-username">用户名</label>
            <input id="student-username" v-model.trim="studentForm.username" type="text" />
          </div>
          <div class="field-stack">
            <label for="student-nickname">昵称</label>
            <input id="student-nickname" v-model.trim="studentForm.nickname" type="text" />
          </div>
          <div class="field-stack form-grid__full">
            <label for="student-password">初始密码</label>
            <input id="student-password" v-model="studentForm.password" type="text" />
          </div>
        </div>
        <div class="modal-actions">
          <button type="button" class="ghost-button" @click="showStudentForm = false">取消</button>
          <button type="button" class="primary-button" :disabled="loading" @click="saveStudent">{{ loading ? '保存中...' : '创建学生' }}</button>
        </div>
      </div>
    </div>

    <div v-if="showStudentImportForm" class="overlay" @click.self="showStudentImportForm = false">
      <div class="modal surface-card surface-card--strong">
        <div class="workspace-head">
          <div>
            <h3>批量导入学生</h3>
            <p>按 JSON 数组格式提交用户名、昵称和密码。</p>
          </div>
          <button type="button" class="inline-clear" @click="showStudentImportForm = false">关闭</button>
        </div>
        <div class="field-stack">
          <label for="student-import-json">学生 JSON 数组</label>
          <textarea id="student-import-json" v-model="studentImportText" rows="12" />
        </div>
        <div class="modal-actions">
          <button type="button" class="ghost-button" @click="showStudentImportForm = false">取消</button>
          <button type="button" class="primary-button" :disabled="loading" @click="saveStudentImport">{{ loading ? '导入中...' : '执行导入' }}</button>
        </div>
      </div>
    </div>

    <div v-if="showPvpForm" class="overlay" @click.self="showPvpForm = false">
      <div class="modal surface-card surface-card--strong">
        <div class="workspace-head">
          <div>
            <h3>{{ editingPvpRoomId !== null ? '编辑竞技房间' : '新建竞技房间' }}</h3>
            <p>通过房间配置一次性控制题量、成员和对战时限。</p>
          </div>
          <button type="button" class="inline-clear" @click="showPvpForm = false">关闭</button>
        </div>
        <div class="form-grid">
          <div class="field-stack">
            <label for="pvp-title">房间名称</label>
            <input id="pvp-title" v-model="pvpForm.title" type="text" />
          </div>
          <div class="field-stack">
            <label for="pvp-description">房间说明</label>
            <input id="pvp-description" v-model="pvpForm.description" type="text" />
          </div>
          <div class="field-stack">
            <label for="pvp-size">人数上限</label>
            <input id="pvp-size" v-model.number="pvpForm.group_size" type="number" min="2" max="12" />
          </div>
          <div class="field-stack">
            <label for="pvp-question-count">题数</label>
            <input id="pvp-question-count" v-model.number="pvpForm.question_count" type="number" min="2" max="50" />
          </div>
          <div class="field-stack">
            <label for="pvp-timer">总时限（秒）</label>
            <input id="pvp-timer" v-model.number="pvpForm.battle_time_limit_seconds" type="number" min="0" max="3600" placeholder="0 = 不限时" />
          </div>
          <div class="field-stack form-grid__full">
            <label for="pvp-student-filter">参赛学生</label>
            <details class="multi-select-card" open>
              <summary class="multi-select-card__summary">
                <span>{{ pvpStudentSummary }}</span>
                <span class="toolbar-chip">{{ pvpForm.member_user_ids.length }} 已选</span>
              </summary>
              <div class="multi-select-card__panel">
                <div class="multi-select-card__toolbar">
                  <input
                    id="pvp-student-filter"
                    v-model="pvpStudentFilter"
                    type="search"
                    placeholder="按昵称、用户名或 ID 筛选学生"
                  />
                  <div class="multi-select-card__actions">
                    <button type="button" class="inline-clear" @click="selectAllVisiblePvpStudents">全选当前结果</button>
                    <button type="button" class="inline-clear" @click="clearPvpStudents">清空</button>
                  </div>
                </div>
                <p class="selector-hint">直接勾选参赛学生，不再手动填写数字编号。</p>
                <div v-if="pvpSelectorLoading" class="selector-empty">学生列表加载中...</div>
                <div v-else-if="filteredPvpStudents.length === 0" class="selector-empty">没有匹配的学生。</div>
                <div v-else class="multi-select-card__list">
                  <label v-for="student in filteredPvpStudents" :key="student.user_id" class="selector-option">
                    <input
                      :checked="pvpForm.member_user_ids.includes(student.user_id)"
                      type="checkbox"
                      @change="handlePvpCheckboxChange('member_user_ids', student.user_id, $event)"
                    />
                    <div class="selector-option__body">
                      <strong>{{ student.nickname }}</strong>
                      <span>{{ student.username }} · ID {{ student.user_id }}</span>
                    </div>
                    <span v-if="!student.is_active" class="status-pill status-pill--warn">已禁用</span>
                  </label>
                </div>
              </div>
            </details>
          </div>
          <div class="field-stack form-grid__full">
            <label for="pvp-unit-filter">出题单元</label>
            <details class="multi-select-card" open>
              <summary class="multi-select-card__summary">
                <span>{{ pvpUnitSummary }}</span>
                <span class="toolbar-chip">{{ pvpForm.question_unit_ids.length }} 已选</span>
              </summary>
              <div class="multi-select-card__panel">
                <div class="multi-select-card__toolbar">
                  <input
                    id="pvp-unit-filter"
                    v-model="pvpUnitFilter"
                    type="search"
                    placeholder="按单元名称、说明或 ID 筛选"
                  />
                  <div class="multi-select-card__actions">
                    <button type="button" class="inline-clear" @click="selectAllVisiblePvpUnits">全选当前结果</button>
                    <button type="button" class="inline-clear" @click="clearPvpUnits">清空</button>
                  </div>
                </div>
                <p class="selector-hint">按单元选择出题范围，保存时会直接提交选中的单元。</p>
                <div v-if="pvpSelectorLoading && units.length === 0" class="selector-empty">单元列表加载中...</div>
                <div v-else-if="filteredPvpUnits.length === 0" class="selector-empty">没有匹配的单元。</div>
                <div v-else class="multi-select-card__list">
                  <label v-for="unit in filteredPvpUnits" :key="unit.id" class="selector-option">
                    <input
                      :checked="pvpForm.question_unit_ids.includes(unit.id)"
                      type="checkbox"
                      @change="handlePvpCheckboxChange('question_unit_ids', unit.id, $event)"
                    />
                    <div class="selector-option__body">
                      <strong>{{ unit.name }}</strong>
                      <span>{{ unit.subtitle || '无副标题' }} · {{ unitLevelCount(unit) }} 个关卡 · ID {{ unit.id }}</span>
                    </div>
                  </label>
                </div>
              </div>
            </details>
          </div>
        </div>
        <div class="modal-actions">
          <button type="button" class="ghost-button" @click="showPvpForm = false">取消</button>
          <button type="button" class="primary-button" :disabled="loading" @click="savePvpRoom">{{ loading ? '保存中...' : '保存房间' }}</button>
        </div>
      </div>
    </div>

    <div v-if="showPasswordForm && !adminForcePasswordChange" class="overlay" @click.self="showPasswordForm = false">
      <div class="modal surface-card surface-card--strong">
        <div class="workspace-head">
          <div>
            <h3>修改管理员密码</h3>
            <p>修改后当前会话会同步刷新。</p>
          </div>
          <button type="button" class="inline-clear" @click="showPasswordForm = false">关闭</button>
        </div>
        <div class="form-grid">
          <div class="field-stack">
            <label for="admin-old-password">旧密码</label>
            <input id="admin-old-password" v-model="passwordForm.old_password" type="password" />
          </div>
          <div class="field-stack">
            <label for="admin-new-password">新密码</label>
            <input id="admin-new-password" v-model="passwordForm.new_password" type="password" />
          </div>
        </div>
        <p v-if="passwordMsg" class="password-msg" :class="{ 'msg-error': passwordMsg !== '密码已修改。' }">{{ passwordMsg }}</p>
        <div class="modal-actions">
          <button type="button" class="ghost-button" @click="showPasswordForm = false">取消</button>
          <button type="button" class="primary-button" :disabled="changingPassword" @click="handleChangePassword">
            {{ changingPassword ? '处理中...' : '确认修改' }}
          </button>
        </div>
      </div>
    </div>

    <div v-if="confirmDialog" class="overlay" @click.self="confirmDialog = null">
      <div class="modal surface-card surface-card--strong modal--compact">
        <div class="workspace-head">
          <div>
            <h3>{{ confirmDialog.title }}</h3>
            <p>{{ confirmDialog.message }}</p>
          </div>
        </div>
        <div class="modal-actions">
          <button type="button" class="ghost-button" @click="confirmDialog = null">取消</button>
          <button
            type="button"
            :class="confirmDialog.tone === 'danger' ? 'danger-button' : 'primary-button'"
            @click="submitConfirmAction"
          >
            {{ confirmDialog.confirmLabel }}
          </button>
        </div>
      </div>
    </div>
  </AdminShell>
</template>

<style scoped>
.admin-login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background:
    radial-gradient(circle at 16% 16%, rgba(30, 64, 175, 0.12), transparent 24%),
    linear-gradient(180deg, #f8fafc 0%, #e8eff5 100%);
}

.admin-login-card {
  width: min(520px, 100%);
  padding: 30px;
  border-radius: 22px;
}

.admin-login-card__meta {
  display: grid;
  grid-template-columns: 72px minmax(0, 1fr);
  gap: 18px;
  margin-bottom: 24px;
}

.admin-login-card__eyebrow,
.page-intro__eyebrow {
  display: block;
  color: #64748b;
  font-size: 11px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.admin-login-card strong,
.page-intro h2,
.workspace-head h3,
.workspace-head h4,
.detail-section h4 {
  color: #0f172a;
}

.admin-login-card strong {
  display: block;
  margin-top: 8px;
  font-size: 28px;
  line-height: 1.1;
}

.admin-login-card p {
  margin: 10px 0 0;
  color: #64748b;
}

.admin-login-form__submit {
  width: 100%;
}

.page-intro,
.admin-workspace-card,
.admin-urgent-panel {
  padding: 22px;
  border-radius: 18px;
}

.page-intro {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.page-intro h2 {
  margin: 8px 0 0;
  font-size: 28px;
  line-height: 1.1;
  letter-spacing: -0.04em;
}

.page-intro p {
  margin: 10px 0 0;
  color: #64748b;
}

.page-intro__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: flex-end;
}

.admin-urgent-panel {
  display: grid;
  gap: 16px;
  border: 1px solid rgba(245, 158, 11, 0.34);
  background: linear-gradient(180deg, rgba(255, 251, 235, 0.96), #ffffff);
}

.admin-urgent-panel h3 {
  margin: 0 0 8px;
}

.admin-urgent-panel p {
  margin: 0;
  color: #92400e;
}

.admin-urgent-panel__actions {
  display: grid;
  gap: 12px;
  max-width: 420px;
}

.feedback-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 16px;
  border-radius: 16px;
  border: 1px solid transparent;
}

.feedback-banner.is-success {
  border-color: rgba(34, 197, 94, 0.28);
  background: rgba(220, 252, 231, 0.88);
  color: #166534;
}

.feedback-banner.is-error {
  border-color: rgba(239, 68, 68, 0.24);
  background: rgba(254, 226, 226, 0.92);
  color: #991b1b;
}

.inline-clear {
  border: none;
  background: none;
  color: inherit;
  cursor: pointer;
}

.workspace-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
}

.workspace-head h3,
.workspace-head h4,
.detail-section h4 {
  margin: 0;
  font-size: 18px;
}

.workspace-head p {
  margin: 6px 0 0;
  color: #64748b;
  font-size: 13px;
}

.workspace-head--compact {
  margin-bottom: 14px;
}

.admin-kpi-grid {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 14px;
}

.admin-kpi-card {
  display: grid;
  gap: 8px;
  padding: 18px;
  border: 1px solid #dbe4ee;
  border-radius: 16px;
  background: linear-gradient(180deg, #ffffff, #f8fbff);
}

.admin-kpi-card__label {
  color: #64748b;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.admin-kpi-card__value {
  font-size: 28px;
  line-height: 1;
  color: #0f172a;
}

.admin-kpi-card__hint {
  color: #64748b;
  font-size: 12px;
}

.dashboard-layout,
.workspace-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.6fr) minmax(320px, 0.92fr);
  gap: 18px;
}

.dashboard-layout__main,
.dashboard-layout__side,
.workspace-side-column {
  display: grid;
  gap: 18px;
  align-content: start;
}

.workspace-card-main,
.workspace-side-card {
  min-width: 0;
}

.dashboard-chart-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.admin-subcard {
  padding: 18px;
  border-radius: 16px;
  border: 1px solid #e2e8f0;
  background: #fbfdff;
}

.quick-action-list {
  display: grid;
  gap: 12px;
}

.quick-action-card {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  width: 100%;
  padding: 16px;
  border-radius: 16px;
  border: 1px solid #dbe4ee;
  background: linear-gradient(180deg, #ffffff, #f8fbff);
  text-align: left;
}

.quick-action-card strong,
.table-title-cell strong,
.detail-profile strong,
.import-step-card strong {
  display: block;
  color: #0f172a;
}

.quick-action-card p,
.table-title-cell span,
.detail-profile span,
.alert-list__item span,
.knowledge-stack p,
.question-preview,
.import-step-card p {
  margin: 6px 0 0;
  color: #64748b;
}

.quick-action-card__meta {
  align-self: flex-start;
  color: #1e40af;
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 700;
}

.alert-list {
  display: grid;
  gap: 10px;
  margin-top: 18px;
}

.alert-list__item,
.room-list__item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  width: 100%;
  padding: 14px 16px;
  border-radius: 16px;
  border: 1px solid #dbe4ee;
  background: #ffffff;
  text-align: left;
}

.admin-filter-bar {
  display: grid;
  grid-template-columns: minmax(220px, 1.5fr) repeat(2, minmax(150px, 0.7fr)) auto;
  gap: 14px;
  margin-bottom: 18px;
}

.admin-filter-bar--wide {
  grid-template-columns: minmax(220px, 1.6fr) minmax(180px, 0.8fr) minmax(150px, 0.7fr) auto;
}

.toggle-control {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border: 1px solid #dbe4ee;
  border-radius: 14px;
  background: #ffffff;
  color: #334155;
  font-size: 13px;
  font-weight: 600;
}

.toggle-control--inline {
  align-self: end;
}

.toggle-control input {
  width: auto;
  min-height: auto;
}

.admin-table tbody tr {
  cursor: pointer;
}

.admin-table tbody tr:hover {
  background: rgba(37, 99, 235, 0.04);
}

.admin-table tbody tr.is-selected {
  background: rgba(30, 64, 175, 0.08);
}

.table-title-cell {
  display: grid;
  gap: 4px;
}

.workspace-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  margin-top: 18px;
}

.workspace-side-card {
  position: sticky;
  top: 16px;
}

.detail-stack {
  display: grid;
  gap: 18px;
}

.detail-profile {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
}

.detail-metric-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.detail-metric-card {
  padding: 14px;
  border: 1px solid #dbe4ee;
  border-radius: 14px;
  background: #fbfdff;
}

.detail-metric-card span {
  display: block;
  color: #64748b;
  font-size: 12px;
}

.detail-metric-card strong {
  display: block;
  margin-top: 8px;
  color: #0f172a;
  font-size: 18px;
}

.detail-section {
  display: grid;
  gap: 10px;
}

.detail-section__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.detail-section__head span {
  color: #64748b;
  font-size: 12px;
}

.side-actions,
.modal-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.compact-scroll {
  max-height: 320px;
}

.question-content,
.question-preview {
  min-width: 0;
  line-height: 1.6;
}

.option-list,
.option-grid {
  display: grid;
  gap: 10px;
}

.option-list__item {
  display: grid;
  grid-template-columns: 28px minmax(0, 1fr);
  gap: 10px;
  padding: 12px 14px;
  border-radius: 14px;
  border: 1px solid #dbe4ee;
  background: #fbfdff;
}

.option-list__item strong {
  color: #1e40af;
}

.knowledge-stack {
  display: grid;
  gap: 8px;
}

.knowledge-stack p {
  margin: 0;
}

.room-list {
  display: grid;
  gap: 12px;
}

.room-list__item {
  display: grid;
  gap: 12px;
}

.room-list__item.is-selected {
  border-color: rgba(37, 99, 235, 0.28);
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.08);
}

.room-list__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.room-list__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  color: #64748b;
  font-size: 12px;
}

.room-group {
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  margin-bottom: 10px;
  background: #fafcfd;
}

.room-group[open] {
  box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.06);
}

.room-group__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 16px;
  cursor: pointer;
  list-style: none;
  font-weight: 700;
  color: #334155;
  user-select: none;
}

.room-group__head::-webkit-details-marker {
  display: none;
}

.room-group__head--finished {
  color: #94a3b8;
}

.admin-rank-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 38px;
  height: 20px;
  margin-right: 6px;
  padding: 0 6px;
  border-radius: 999px;
  background: rgba(0, 122, 255, 0.1);
  color: #007AFF;
  font-size: 11px;
  font-weight: 700;
}

.room-group__empty {
  padding: 12px 16px;
  color: #94a3b8;
  font-size: 13px;
}

.import-flow {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.import-step-card {
  display: grid;
  grid-template-columns: 54px minmax(0, 1fr);
  gap: 14px;
  padding: 18px;
  border-radius: 16px;
  border: 1px solid #dbe4ee;
  background: #fbfdff;
}

.import-step-card__index {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 54px;
  height: 54px;
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(30, 64, 175, 0.12), rgba(59, 130, 246, 0.18));
  color: #1e40af;
  font-family: var(--font-mono);
  font-size: 16px;
  font-weight: 700;
}

.import-drop-zone {
  display: grid;
  gap: 10px;
  padding: 18px;
  border-radius: 16px;
  border: 1px dashed #94a3b8;
  background: #f8fafc;
  margin-bottom: 16px;
}

.import-file-hint {
  margin: 0 0 18px;
  color: #64748b;
  font-size: 13px;
}

.overlay {
  position: fixed;
  inset: 0;
  z-index: 80;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background: rgba(15, 23, 42, 0.48);
}

.modal {
  width: min(860px, 100%);
  max-height: calc(100vh - 40px);
  padding: 22px;
  border-radius: 20px;
  overflow-y: auto;
  animation: scaleIn 0.22s var(--ease-fluid);
}

.modal--compact {
  width: min(480px, 100%);
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.form-grid__full {
  grid-column: 1 / -1;
}

.multi-select-card {
  border: 1px solid #dbe4ee;
  border-radius: 16px;
  background: #fbfdff;
}

.multi-select-card[open] {
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.08);
}

.multi-select-card__summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 16px;
  cursor: pointer;
  list-style: none;
  color: #0f172a;
  font-weight: 600;
}

.multi-select-card__summary::-webkit-details-marker {
  display: none;
}

.multi-select-card__panel {
  display: grid;
  gap: 12px;
  padding: 0 16px 16px;
}

.multi-select-card__toolbar {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 12px;
  align-items: center;
}

.multi-select-card__actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.multi-select-card__list {
  max-height: 240px;
  overflow: auto;
  display: grid;
  gap: 10px;
  padding-right: 4px;
}

.selector-option {
  display: grid;
  grid-template-columns: 18px minmax(0, 1fr) auto;
  gap: 12px;
  align-items: start;
  padding: 12px 14px;
  border-radius: 14px;
  border: 1px solid #dbe4ee;
  background: #ffffff;
  cursor: pointer;
}

.selector-option:hover {
  border-color: rgba(37, 99, 235, 0.24);
  background: #f8fbff;
}

.selector-option__body {
  display: grid;
  gap: 4px;
}

.selector-option__body strong {
  color: #0f172a;
}

.selector-option__body span,
.selector-hint,
.selector-empty {
  color: #64748b;
  font-size: 13px;
}

.selector-hint,
.selector-empty {
  margin: 0;
}

.mono-number {
  font-family: var(--font-mono);
}

.toolbar-chip-active {
  border-color: rgba(37, 99, 235, 0.24);
  background: rgba(37, 99, 235, 0.08);
  color: #1e40af;
}

.msg-error {
  color: #b91c1c;
}

.password-msg {
  margin: 0;
  color: #1d4ed8;
}

textarea {
  min-height: 120px;
  resize: vertical;
}

@media (max-width: 1380px) {
  .admin-kpi-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .dashboard-layout,
  .workspace-layout {
    grid-template-columns: 1fr;
  }

  .workspace-side-card {
    position: static;
  }
}

@media (max-width: 1120px) {
  .dashboard-chart-grid,
  .import-flow {
    grid-template-columns: 1fr;
  }

  .admin-filter-bar,
  .admin-filter-bar--wide {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 760px) {
  .page-intro,
  .workspace-head,
  .workspace-footer,
  .side-actions,
  .modal-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .page-intro__meta {
    justify-content: flex-start;
  }

  .admin-kpi-grid,
  .detail-metric-grid,
  .form-grid,
  .admin-filter-bar,
  .admin-filter-bar--wide {
    grid-template-columns: 1fr;
  }

  .admin-login-card__meta {
    grid-template-columns: 1fr;
  }

  .import-step-card {
    grid-template-columns: 1fr;
  }

  .multi-select-card__toolbar,
  .selector-option {
    grid-template-columns: 1fr;
  }

  .multi-select-card__actions {
    justify-content: flex-start;
  }
}

@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation: none !important;
    transition: none !important;
    scroll-behavior: auto !important;
  }
}
</style>

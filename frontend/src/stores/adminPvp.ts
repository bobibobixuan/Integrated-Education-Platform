import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import {
  createPvpRoom,
  fetchPvpRooms,
  fetchStudents,
  finishPvpRoom,
  startPvpRoom,
  updatePvpRoom,
} from '@/api/admin'
import { fetchUnits } from '@/api/game'
import type { AdminPvpRoomCreate, AdminStudent, PvpMember, PvpRoom, UnitOut } from '@/types/api'

const ADMIN_TOKEN_KEY = 'admin_token'
const LEGACY_ADMIN_TOKEN_KEY = 'admin_jwt_token'

export interface PvpRoomFormState {
  title: string
  description: string
  group_size: number
  member_user_ids: number[]
  question_unit_ids: number[]
  question_count: number
  battle_time_limit_seconds: number
}

function readAdminToken() {
  return localStorage.getItem(ADMIN_TOKEN_KEY) || localStorage.getItem(LEGACY_ADMIN_TOKEN_KEY)
}

function getErrorMessage(error: unknown) {
  return error instanceof Error ? error.message : '操作失败，请稍后重试。'
}

function createEmptyPvpForm(): PvpRoomFormState {
  return {
    title: '',
    description: '',
    group_size: 6,
    member_user_ids: [],
    question_unit_ids: [],
    question_count: 10,
    battle_time_limit_seconds: 300,
  }
}

function copyRoomToForm(room: PvpRoom): PvpRoomFormState {
  return {
    title: room.title,
    description: room.description || '',
    group_size: room.group_size,
    member_user_ids: room.members.map(member => member.user_id),
    question_unit_ids: [...room.question_unit_ids],
    question_count: room.question_count,
    battle_time_limit_seconds: room.battle_time_limit_seconds,
  }
}

function getAdminWsUrl() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${protocol}//${window.location.host}/ws/online`
}

function formatNumber(value: number | null | undefined) {
  return new Intl.NumberFormat('zh-CN').format(Number(value ?? 0))
}

function formatSeconds(value: number | null | undefined) {
  const number = Number(value ?? 0)
  return number <= 0 ? '不限时' : `${number.toFixed(number % 1 === 0 ? 0 : 1)}s`
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

function formatPercent(value: number | null | undefined) {
  const number = Number(value ?? 0)
  return `${number.toFixed(number % 1 === 0 ? 0 : 1)}%`
}

function roomStatusLabel(status: string) {
  if (status === 'waiting') return '待开始'
  if (status === 'countdown') return '倒计时'
  if (status === 'running') return '进行中'
  if (status === 'finished') return '已结束'
  return status
}

function roomStatusType(status: string): 'success' | 'warning' | 'info' | 'danger' {
  if (status === 'running') return 'success'
  if (status === 'waiting' || status === 'countdown') return 'warning'
  if (status === 'finished') return 'info'
  return 'danger'
}

export const useAdminPvpStore = defineStore('adminPvp', () => {
  const loading = ref(false)
  const saving = ref(false)
  const selectorLoading = ref(false)
  const error = ref('')
  const pvpRooms = ref<PvpRoom[]>([])
  const selectedRoomId = ref<number | null>(null)
  const editingRoomId = ref<number | null>(null)
  const roomForm = ref<PvpRoomFormState>(createEmptyPvpForm())
  const selectableStudents = ref<AdminStudent[]>([])
  const units = ref<UnitOut[]>([])
  const socketReady = ref(false)
  const lastSnapshotAt = ref<string | null>(null)
  const socket = ref<WebSocket | null>(null)
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null
  let reconnectAttempts = 0

  const rooms = computed(() => pvpRooms.value)
  const selectedRoom = computed(() => pvpRooms.value.find(item => item.id === selectedRoomId.value) ?? null)
  const waitingRooms = computed(() => pvpRooms.value.filter(room => room.status === 'waiting' || room.status === 'countdown'))
  const runningRooms = computed(() => pvpRooms.value.filter(room => room.status === 'running'))
  const finishedRooms = computed(() => pvpRooms.value.filter(room => room.status === 'finished'))
  const groupedRooms = computed(() => ({
    waiting: waitingRooms.value,
    running: runningRooms.value,
    finished: finishedRooms.value,
  }))
  const activeRooms = computed(() => pvpRooms.value.filter(room => room.status !== 'finished'))
  const selectedRoomMembers = computed(() => (
    selectedRoom.value?.members.slice().sort((a, b) => a.rank - b.rank || a.seat_order - b.seat_order) ?? []
  ))
  const selectedRoomLogs = computed(() => (
    selectedRoom.value?.logs.slice().sort((a, b) => {
      const aTime = a.created_at ? new Date(a.created_at).getTime() : 0
      const bTime = b.created_at ? new Date(b.created_at).getTime() : 0
      return bTime - aTime
    }) ?? []
  ))
  const selectedRoomStatusText = computed(() => roomStatusLabel(selectedRoom.value?.status ?? ''))
  const canStartSelectedRoom = computed(() => selectedRoom.value?.status === 'waiting')
  const canFinishSelectedRoom = computed(() => selectedRoom.value?.status === 'running')
  const pvpOverview = computed(() => {
    const onlineIds = new Set<number>()
    pvpRooms.value.forEach(room => {
      room.members.forEach(member => {
        if (member.is_online) onlineIds.add(member.user_id)
      })
    })
    return {
      total: pvpRooms.value.length,
      waiting: waitingRooms.value.length,
      running: runningRooms.value.length,
      finished: finishedRooms.value.length,
      onlineMembers: onlineIds.size,
      lastSnapshotAt: lastSnapshotAt.value,
    }
  })
  const selectedRoomProgress = computed(() => {
    const room = selectedRoom.value
    if (!room) {
      return {
        totalQuestions: 0,
        answeredCount: 0,
        submittedMembers: 0,
        averageAccuracy: null as number | null,
        leader: null as PvpMember | null,
      }
    }

    const members = selectedRoomMembers.value
    const submittedMembers = members.filter(member => member.answered_count > 0).length
    const answeredCount = members.reduce((sum, member) => sum + Number(member.answered_count ?? 0), 0)
    const accuracyMembers = members.filter(member => Number.isFinite(Number(member.accuracy)))
    const averageAccuracy = accuracyMembers.length > 0
      ? accuracyMembers.reduce((sum, member) => sum + Number(member.accuracy ?? 0), 0) / accuracyMembers.length
      : null

    return {
      totalQuestions: room.question_count,
      answeredCount,
      submittedMembers,
      averageAccuracy,
      leader: members[0] ?? null,
    }
  })
  const sortedStudents = computed(() => (
    selectableStudents.value.slice().sort((a, b) => a.nickname.localeCompare(b.nickname, 'zh-CN', { numeric: true }))
  ))

  function syncSelectedRoom() {
    if (!pvpRooms.value.some(item => item.id === selectedRoomId.value)) {
      selectedRoomId.value = pvpRooms.value[0]?.id ?? null
    }
  }

  async function loadRooms() {
    const token = readAdminToken()
    if (!token) {
      error.value = '请先登录教师管理后台。'
      pvpRooms.value = []
      selectedRoomId.value = null
      return
    }

    loading.value = true
    error.value = ''
    try {
      pvpRooms.value = await fetchPvpRooms(token)
      lastSnapshotAt.value = new Date().toISOString()
      syncSelectedRoom()
    } catch (err) {
      error.value = getErrorMessage(err)
    } finally {
      loading.value = false
    }
  }

  async function ensureUnitsLoaded() {
    if (units.value.length > 0) return
    const token = readAdminToken()
    if (!token) throw new Error('请先登录教师管理后台。')
    units.value = await fetchUnits(token)
  }

  async function loadFormOptions() {
    const token = readAdminToken()
    if (!token) throw new Error('请先登录教师管理后台。')

    selectorLoading.value = true
    error.value = ''
    try {
      await ensureUnitsLoaded()
      const allStudents: AdminStudent[] = []
      let page = 1
      const pageSize = 100
      while (true) {
        const res = await fetchStudents(token, page, pageSize, '', 'total_score', 'desc', true)
        allStudents.push(...res.items)
        if (allStudents.length >= res.total || res.items.length < pageSize) break
        page += 1
      }
      selectableStudents.value = allStudents
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      selectorLoading.value = false
    }
  }

  async function openNewRoomForm() {
    editingRoomId.value = null
    roomForm.value = createEmptyPvpForm()
    await loadFormOptions()
  }

  async function openEditRoomForm(room: PvpRoom) {
    editingRoomId.value = room.id
    roomForm.value = copyRoomToForm(room)
    await loadFormOptions()
  }

  function buildRoomPayload(): AdminPvpRoomCreate {
    return {
      title: roomForm.value.title.trim(),
      description: roomForm.value.description.trim(),
      group_size: roomForm.value.group_size,
      member_user_ids: [...roomForm.value.member_user_ids],
      question_unit_ids: [...roomForm.value.question_unit_ids],
      question_count: roomForm.value.question_count,
      battle_time_limit_seconds: roomForm.value.battle_time_limit_seconds,
    }
  }

  async function saveRoom() {
    const token = readAdminToken()
    if (!token) throw new Error('请先登录教师管理后台。')

    saving.value = true
    error.value = ''
    try {
      if (editingRoomId.value !== null) {
        await updatePvpRoom(token, editingRoomId.value, buildRoomPayload())
      } else {
        await createPvpRoom(token, buildRoomPayload())
      }
      await loadRooms()
      requestRoomsSnapshot()
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      saving.value = false
    }
  }

  async function startRoom(roomId: number) {
    const token = readAdminToken()
    if (!token) throw new Error('请先登录教师管理后台。')

    saving.value = true
    error.value = ''
    try {
      await startPvpRoom(token, roomId)
      await loadRooms()
      requestRoomsSnapshot()
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      saving.value = false
    }
  }

  async function finishRoom(roomId: number) {
    const token = readAdminToken()
    if (!token) throw new Error('请先登录教师管理后台。')

    saving.value = true
    error.value = ''
    try {
      await finishPvpRoom(token, roomId)
      await loadRooms()
      requestRoomsSnapshot()
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      saving.value = false
    }
  }

  function clearReconnectTimer() {
    if (!reconnectTimer) return
    clearTimeout(reconnectTimer)
    reconnectTimer = null
  }

  function requestRoomsSnapshot() {
    const current = socket.value
    if (!current || current.readyState !== WebSocket.OPEN || !socketReady.value) return
    current.send(JSON.stringify({ type: 'request_pvp_rooms' }))
  }

  function scheduleReconnect() {
    if (!readAdminToken()) return
    clearReconnectTimer()
    const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000)
    reconnectAttempts += 1
    reconnectTimer = setTimeout(() => {
      connectSocket()
    }, delay)
  }

  function closeSocket() {
    clearReconnectTimer()
    reconnectAttempts = 0
    socketReady.value = false
    const current = socket.value
    socket.value = null
    if (!current) return
    current.onopen = null
    current.onmessage = null
    current.onclose = null
    current.onerror = null
    if (current.readyState === WebSocket.OPEN || current.readyState === WebSocket.CONNECTING) {
      current.close(1000, 'admin pvp page closed')
    }
  }

  function connectSocket() {
    const token = readAdminToken()
    if (!token) return
    const current = socket.value
    if (current && (current.readyState === WebSocket.OPEN || current.readyState === WebSocket.CONNECTING)) {
      if (socketReady.value) requestRoomsSnapshot()
      return
    }

    clearReconnectTimer()
    socketReady.value = false
    const ws = new WebSocket(getAdminWsUrl())
    socket.value = ws

    ws.onopen = () => {
      reconnectAttempts = 0
      ws.send(JSON.stringify({ type: 'auth', token }))
    }

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data) as { type?: string; status?: string; rooms?: PvpRoom[] }
        if (msg.type === 'auth_state') {
          socketReady.value = msg.status === 'authenticated'
          if (socketReady.value) requestRoomsSnapshot()
          return
        }
        if (msg.type === 'pvp_rooms' && Array.isArray(msg.rooms)) {
          pvpRooms.value = msg.rooms
          lastSnapshotAt.value = new Date().toISOString()
          syncSelectedRoom()
        }
      } catch {
        // Ignore malformed socket messages.
      }
    }

    ws.onclose = (event) => {
      if (socket.value === ws) {
        socket.value = null
        socketReady.value = false
      }
      if (event.code !== 1000) {
        scheduleReconnect()
      }
    }

    ws.onerror = () => {
      // The close handler owns reconnect scheduling.
    }
  }

  return {
    loading,
    saving,
    selectorLoading,
    error,
    pvpRooms,
    rooms,
    selectedRoomId,
    selectedRoom,
    groupedRooms,
    activeRooms,
    editingRoomId,
    roomForm,
    selectableStudents,
    sortedStudents,
    units,
    socketReady,
    lastSnapshotAt,
    waitingRooms,
    runningRooms,
    finishedRooms,
    selectedRoomMembers,
    selectedRoomLogs,
    selectedRoomStatusText,
    canStartSelectedRoom,
    canFinishSelectedRoom,
    pvpOverview,
    selectedRoomProgress,
    formatNumber,
    formatSeconds,
    formatDateTime,
    formatPercent,
    roomStatusLabel,
    roomStatusType,
    loadRooms,
    loadFormOptions,
    openNewRoomForm,
    openEditRoomForm,
    saveRoom,
    startRoom,
    finishRoom,
    connectSocket,
    closeSocket,
    requestRoomsSnapshot,
  }
})

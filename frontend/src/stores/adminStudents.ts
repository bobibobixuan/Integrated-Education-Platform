import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import {
  createStudent,
  disableStudent,
  fetchStudentDetail,
  fetchStudents,
  updateStudent,
} from '@/api/admin'
import type { AdminStudent, AdminStudentDetail } from '@/types/api'

const ADMIN_TOKEN_KEY = 'admin_token'
const LEGACY_ADMIN_TOKEN_KEY = 'admin_jwt_token'
const PAGE_SIZE = 20

type StudentStatusFilter = 'active' | 'all' | 'disabled'
type StudentSortBy = 'total_score' | 'accuracy' | 'total_questions'
type SortOrder = 'desc' | 'asc'

interface StudentCreateForm {
  username: string
  nickname: string
  password: string
}

interface StudentUpdateForm {
  nickname: string
  new_password: string
}

function readAdminToken() {
  return localStorage.getItem(ADMIN_TOKEN_KEY) || localStorage.getItem(LEGACY_ADMIN_TOKEN_KEY)
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

export const useAdminStudentsStore = defineStore('adminStudents', () => {
  const loading = ref(false)
  const detailLoading = ref(false)
  const saving = ref(false)
  const error = ref('')
  const students = ref<AdminStudent[]>([])
  const total = ref(0)
  const page = ref(1)
  const search = ref('')
  const status = ref<StudentStatusFilter>('active')
  const sortBy = ref<StudentSortBy>('total_score')
  const order = ref<SortOrder>('desc')
  const selectedStudentId = ref<number | null>(null)
  const studentDetail = ref<AdminStudentDetail | null>(null)

  const includeDisabled = computed(() => status.value !== 'active')
  const selectedStudent = computed(() => students.value.find(item => item.user_id === selectedStudentId.value) ?? null)
  const filteredStudents = computed(() => {
    if (status.value === 'disabled') return students.value.filter(student => !student.is_active)
    if (status.value === 'active') return students.value.filter(student => student.is_active)
    return students.value
  })
  const hasPreviousPage = computed(() => page.value > 1)
  const hasNextPage = computed(() => page.value * PAGE_SIZE < total.value)
  const studentAccuracy = computed(() => {
    if (!studentDetail.value || studentDetail.value.total_questions === 0) return '0%'
    return formatPercent((studentDetail.value.total_correct / studentDetail.value.total_questions) * 100)
  })

  async function loadStudents(options: { keepSelection?: boolean } = {}) {
    const token = readAdminToken()
    if (!token) {
      error.value = '请先登录教师管理后台。'
      students.value = []
      total.value = 0
      selectedStudentId.value = null
      studentDetail.value = null
      return
    }

    loading.value = true
    error.value = ''
    try {
      const res = await fetchStudents(
        token,
        page.value,
        PAGE_SIZE,
        search.value,
        sortBy.value,
        order.value,
        includeDisabled.value,
      )
      students.value = res.items
      total.value = res.total

      const currentSelected = selectedStudentId.value && res.items.some(item => item.user_id === selectedStudentId.value)
      if (res.items.length === 0) {
        selectedStudentId.value = null
        studentDetail.value = null
        return
      }

      if (!options.keepSelection || !currentSelected) {
        selectedStudentId.value = res.items[0].user_id
      }

      if (selectedStudentId.value !== null) {
        await loadStudentDetail(selectedStudentId.value)
      }
    } catch (err) {
      error.value = getErrorMessage(err)
    } finally {
      loading.value = false
    }
  }

  async function loadStudentDetail(userId: number) {
    const token = readAdminToken()
    if (!token) {
      error.value = '请先登录教师管理后台。'
      return
    }

    selectedStudentId.value = userId
    detailLoading.value = true
    error.value = ''
    try {
      studentDetail.value = await fetchStudentDetail(token, userId)
    } catch (err) {
      error.value = getErrorMessage(err)
    } finally {
      detailLoading.value = false
    }
  }

  async function applyFilters() {
    page.value = 1
    await loadStudents()
  }

  async function goPreviousPage() {
    if (!hasPreviousPage.value) return
    page.value -= 1
    await loadStudents({ keepSelection: true })
  }

  async function goNextPage() {
    if (!hasNextPage.value) return
    page.value += 1
    await loadStudents({ keepSelection: true })
  }

  async function createStudentAccount(form: StudentCreateForm) {
    const token = readAdminToken()
    if (!token) throw new Error('请先登录教师管理后台。')

    saving.value = true
    error.value = ''
    try {
      await createStudent(token, {
        username: form.username.trim(),
        nickname: form.nickname.trim(),
        password: form.password,
      })
      page.value = 1
      await loadStudents()
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      saving.value = false
    }
  }

  async function updateStudentAccount(userId: number, form: StudentUpdateForm) {
    const token = readAdminToken()
    if (!token) throw new Error('请先登录教师管理后台。')

    const body: Record<string, unknown> = {}
    if (form.nickname.trim()) body.nickname = form.nickname.trim()
    if (form.new_password.trim()) body.new_password = form.new_password.trim()

    saving.value = true
    error.value = ''
    try {
      await updateStudent(token, userId, body)
      await loadStudents({ keepSelection: true })
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      saving.value = false
    }
  }

  async function disableStudentAccount(userId: number) {
    const token = readAdminToken()
    if (!token) throw new Error('请先登录教师管理后台。')

    saving.value = true
    error.value = ''
    try {
      await disableStudent(token, userId)
      await loadStudents({ keepSelection: true })
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      saving.value = false
    }
  }

  return {
    loading,
    detailLoading,
    saving,
    error,
    students,
    filteredStudents,
    total,
    page,
    pageSize: PAGE_SIZE,
    search,
    status,
    sortBy,
    order,
    selectedStudentId,
    selectedStudent,
    studentDetail,
    hasPreviousPage,
    hasNextPage,
    studentAccuracy,
    formatNumber,
    formatPercent,
    formatDateTime,
    loadStudents,
    loadStudentDetail,
    applyFilters,
    goPreviousPage,
    goNextPage,
    createStudentAccount,
    updateStudentAccount,
    disableStudentAccount,
  }
})

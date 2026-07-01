import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import {
  createQuestion,
  fetchQuestions,
  importQuestions,
  importQuestionsExcel,
  toggleQuestion,
  updateQuestion,
} from '@/api/admin'
import { fetchUnits } from '@/api/game'
import type {
  AdminQuestion,
  LevelOut,
  QuestionCreatePayload,
  QuestionUpdatePayload,
  UnitOut,
} from '@/types/api'

const ADMIN_TOKEN_KEY = 'admin_token'
const LEGACY_ADMIN_TOKEN_KEY = 'admin_jwt_token'
const PAGE_SIZE = 20

type QuestionStatusFilter = 'active' | 'all' | 'inactive'

export interface QuestionFormState {
  content: string
  type: string
  answer: string
  options: { letter: string; text: string }[]
  level_id: number
  title: string
  knowledge_meaning: string
  knowledge_rule: string
  knowledge_error: string
  knowledge_example: string
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

function createEmptyQuestionForm(): QuestionFormState {
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

function copyQuestionToForm(question: AdminQuestion): QuestionFormState {
  return {
    content: question.content,
    type: question.type,
    answer: question.answer,
    options: (question.options ?? [
      { letter: 'A', text: '' },
      { letter: 'B', text: '' },
      { letter: 'C', text: '' },
      { letter: 'D', text: '' },
    ]).map(option => ({ ...option })),
    level_id: question.level_id,
    title: question.title || '',
    knowledge_meaning: question.knowledge_meaning || '',
    knowledge_rule: question.knowledge_rule || '',
    knowledge_error: question.knowledge_error || '',
    knowledge_example: question.knowledge_example || '',
  }
}

export const useAdminQuestionsStore = defineStore('adminQuestions', () => {
  const activeTab = ref<'list' | 'import'>('list')
  const loading = ref(false)
  const saving = ref(false)
  const importing = ref(false)
  const error = ref('')
  const questions = ref<AdminQuestion[]>([])
  const total = ref(0)
  const page = ref(1)
  const search = ref('')
  const unitId = ref(0)
  const levelId = ref(0)
  const questionType = ref('')
  const status = ref<QuestionStatusFilter>('active')
  const selectedQuestionId = ref<number | null>(null)
  const editingQuestionId = ref<number | null>(null)
  const questionForm = ref<QuestionFormState>(createEmptyQuestionForm())
  const units = ref<UnitOut[]>([])
  const jsonImportText = ref('{\n  "version": "1.0",\n  "unit": "",\n  "questions": []\n}')
  const excelFile = ref<File | null>(null)
  const excelUnit = ref('')
  const excelFileName = ref('')

  const includeInactive = computed(() => status.value !== 'active')
  const selectedQuestion = computed(() => questions.value.find(item => item.id === selectedQuestionId.value) ?? null)
  const filteredQuestions = computed(() => {
    if (status.value === 'inactive') return questions.value.filter(question => !question.is_active)
    if (status.value === 'active') return questions.value.filter(question => question.is_active)
    return questions.value
  })
  const hasPreviousPage = computed(() => page.value > 1)
  const hasNextPage = computed(() => page.value * PAGE_SIZE < total.value)
  const levelOptions = computed(() => units.value.flatMap(unit => {
    if (!Array.isArray(unit.levels)) return []
    return unit.levels.map((level: LevelOut) => ({
      levelId: level.id,
      unitId: unit.id,
      label: `${unit.name} / ${level.name}`,
    }))
  }))
  const filteredLevelOptions = computed(() => (
    unitId.value > 0 ? levelOptions.value.filter(option => option.unitId === unitId.value) : levelOptions.value
  ))

  async function ensureUnitsLoaded() {
    if (units.value.length > 0) return
    const token = readAdminToken()
    if (!token) throw new Error('请先登录教师管理后台。')
    units.value = await fetchUnits(token)
  }

  async function loadQuestions(options: { keepSelection?: boolean } = {}) {
    const token = readAdminToken()
    if (!token) {
      error.value = '请先登录教师管理后台。'
      questions.value = []
      total.value = 0
      selectedQuestionId.value = null
      return
    }

    loading.value = true
    error.value = ''
    try {
      await ensureUnitsLoaded()
      const res = await fetchQuestions(
        token,
        page.value,
        PAGE_SIZE,
        levelId.value > 0 ? levelId.value : undefined,
        unitId.value > 0 ? unitId.value : undefined,
        questionType.value,
        search.value,
        includeInactive.value,
      )
      questions.value = res.items
      total.value = res.total

      const currentSelected = selectedQuestionId.value && res.items.some(item => item.id === selectedQuestionId.value)
      if (res.items.length === 0) {
        selectedQuestionId.value = null
        return
      }
      if (!options.keepSelection || !currentSelected) {
        selectedQuestionId.value = res.items[0].id
      }
    } catch (err) {
      error.value = getErrorMessage(err)
    } finally {
      loading.value = false
    }
  }

  async function applyFilters() {
    page.value = 1
    await loadQuestions()
  }

  async function goPreviousPage() {
    if (!hasPreviousPage.value) return
    page.value -= 1
    await loadQuestions({ keepSelection: true })
  }

  async function goNextPage() {
    if (!hasNextPage.value) return
    page.value += 1
    await loadQuestions({ keepSelection: true })
  }

  function setUnitFilter(value: number) {
    unitId.value = value
    if (levelId.value > 0) {
      const stillValid = filteredLevelOptions.value.some(option => option.levelId === levelId.value)
      if (!stillValid) levelId.value = 0
    }
  }

  function openNewQuestionForm() {
    editingQuestionId.value = null
    questionForm.value = createEmptyQuestionForm()
    questionForm.value.level_id = filteredLevelOptions.value[0]?.levelId ?? levelOptions.value[0]?.levelId ?? 0
  }

  function openEditQuestionForm(question: AdminQuestion) {
    editingQuestionId.value = question.id
    questionForm.value = copyQuestionToForm(question)
  }

  function buildQuestionPayload(): QuestionCreatePayload {
    const form = questionForm.value
    return {
      content: form.content,
      type: form.type,
      answer: form.answer,
      options: (form.type === '选择题' || form.type === '多选题')
        ? form.options.filter(item => item.text.trim())
        : null,
      level_id: form.level_id,
      title: form.title.trim() || form.content.slice(0, 60),
      knowledge_meaning: form.knowledge_meaning.trim(),
      knowledge_rule: form.knowledge_rule.trim(),
      knowledge_error: form.knowledge_error.trim(),
      knowledge_example: form.knowledge_example.trim(),
    }
  }

  async function saveQuestion() {
    const token = readAdminToken()
    if (!token) throw new Error('请先登录教师管理后台。')

    saving.value = true
    error.value = ''
    try {
      const payload = buildQuestionPayload()
      if (editingQuestionId.value !== null) {
        await updateQuestion(token, editingQuestionId.value, payload as QuestionUpdatePayload)
      } else {
        await createQuestion(token, payload)
      }
      await loadQuestions({ keepSelection: true })
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      saving.value = false
    }
  }

  async function toggleQuestionActive(question: AdminQuestion) {
    const token = readAdminToken()
    if (!token) throw new Error('请先登录教师管理后台。')

    saving.value = true
    error.value = ''
    try {
      await toggleQuestion(token, question.id, !question.is_active)
      await loadQuestions({ keepSelection: true })
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      saving.value = false
    }
  }

  async function importJsonQuestions() {
    const token = readAdminToken()
    if (!token) throw new Error('请先登录教师管理后台。')

    importing.value = true
    error.value = ''
    try {
      const payload = JSON.parse(jsonImportText.value) as Record<string, unknown>
      const res = await importQuestions(token, payload)
      await loadQuestions()
      return res.message || 'JSON 题库已导入。'
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      importing.value = false
    }
  }

  function setExcelFile(file: File | null) {
    excelFile.value = file
    excelFileName.value = file?.name ?? ''
    if (file && !excelUnit.value) {
      excelUnit.value = file.name.replace(/\.(xlsx|xlsm)$/i, '')
    }
  }

  async function importExcelQuestions() {
    const token = readAdminToken()
    if (!token) throw new Error('请先登录教师管理后台。')
    if (!excelFile.value) throw new Error('请先选择 Excel 文件。')
    if (!excelUnit.value.trim()) throw new Error('请先填写目标单元名称。')

    importing.value = true
    error.value = ''
    try {
      const res = await importQuestionsExcel(token, excelFile.value, excelUnit.value.trim())
      excelFile.value = null
      excelFileName.value = ''
      excelUnit.value = ''
      await loadQuestions()
      return res.message || 'Excel 题库已导入。'
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      importing.value = false
    }
  }

  async function fillJsonFromFile(file: File) {
    jsonImportText.value = await file.text()
  }

  return {
    activeTab,
    loading,
    saving,
    importing,
    error,
    questions,
    filteredQuestions,
    total,
    page,
    pageSize: PAGE_SIZE,
    search,
    unitId,
    levelId,
    questionType,
    status,
    selectedQuestionId,
    selectedQuestion,
    editingQuestionId,
    questionForm,
    units,
    levelOptions,
    filteredLevelOptions,
    jsonImportText,
    excelFile,
    excelUnit,
    excelFileName,
    hasPreviousPage,
    hasNextPage,
    formatNumber,
    ensureUnitsLoaded,
    loadQuestions,
    applyFilters,
    goPreviousPage,
    goNextPage,
    setUnitFilter,
    openNewQuestionForm,
    openEditQuestionForm,
    saveQuestion,
    toggleQuestionActive,
    importJsonQuestions,
    setExcelFile,
    importExcelQuestions,
    fillJsonFromFile,
  }
})

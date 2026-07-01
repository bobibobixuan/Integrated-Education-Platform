import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

export const DASHBOARD_LAYOUT_KEY = 'admin_dashboard_layout_v1'

export type AdminDashboardWidgetId =
  | 'kpi'
  | 'trend'
  | 'leaderboard'
  | 'riskUnits'
  | 'focusStudents'
  | 'quickActions'

export type AdminDashboardWidgetWidth = 'half' | 'full'

export interface AdminDashboardWidgetConfig {
  id: AdminDashboardWidgetId
  title: string
  visible: boolean
  width: AdminDashboardWidgetWidth
}

const defaultWidgets: AdminDashboardWidgetConfig[] = [
  { id: 'kpi', title: '核心指标', visible: true, width: 'full' },
  { id: 'trend', title: '趋势概览', visible: true, width: 'half' },
  { id: 'leaderboard', title: '排行榜', visible: true, width: 'half' },
  { id: 'riskUnits', title: '风险单元', visible: true, width: 'half' },
  { id: 'focusStudents', title: '重点学生', visible: true, width: 'half' },
  { id: 'quickActions', title: '快捷入口', visible: true, width: 'full' },
]

function cloneDefaultWidgets() {
  return defaultWidgets.map(widget => ({ ...widget }))
}

function normalizeWidgets(rawWidgets: unknown): AdminDashboardWidgetConfig[] {
  if (!Array.isArray(rawWidgets)) return cloneDefaultWidgets()

  const knownWidgets = new Map(defaultWidgets.map(widget => [widget.id, widget]))
  const normalized: AdminDashboardWidgetConfig[] = []
  const seen = new Set<AdminDashboardWidgetId>()

  rawWidgets.forEach(rawWidget => {
    if (!rawWidget || typeof rawWidget !== 'object') return
    const candidate = rawWidget as Partial<AdminDashboardWidgetConfig>
    if (!candidate.id || !knownWidgets.has(candidate.id) || seen.has(candidate.id)) return

    const base = knownWidgets.get(candidate.id)
    if (!base) return

    normalized.push({
      ...base,
      visible: typeof candidate.visible === 'boolean' ? candidate.visible : base.visible,
      width: candidate.width === 'half' || candidate.width === 'full' ? candidate.width : base.width,
    })
    seen.add(candidate.id)
  })

  defaultWidgets.forEach(widget => {
    if (!seen.has(widget.id)) {
      normalized.push({ ...widget })
    }
  })

  return normalized
}

export const useAdminDashboardLayoutStore = defineStore('adminDashboardLayout', () => {
  const widgets = ref<AdminDashboardWidgetConfig[]>(cloneDefaultWidgets())

  const visibleWidgets = computed(() => widgets.value.filter(widget => widget.visible))

  function saveLayout() {
    localStorage.setItem(DASHBOARD_LAYOUT_KEY, JSON.stringify(widgets.value))
  }

  function loadLayout() {
    const raw = localStorage.getItem(DASHBOARD_LAYOUT_KEY)
    if (!raw) {
      widgets.value = cloneDefaultWidgets()
      return
    }

    try {
      widgets.value = normalizeWidgets(JSON.parse(raw))
      saveLayout()
    } catch {
      widgets.value = cloneDefaultWidgets()
      saveLayout()
    }
  }

  function resetLayout() {
    widgets.value = cloneDefaultWidgets()
    saveLayout()
  }

  function toggleWidget(id: AdminDashboardWidgetId, visible: boolean) {
    const widget = widgets.value.find(item => item.id === id)
    if (!widget) return
    widget.visible = visible
    saveLayout()
  }

  function moveWidgetUp(id: AdminDashboardWidgetId) {
    const index = widgets.value.findIndex(widget => widget.id === id)
    if (index <= 0) return
    const nextWidgets = [...widgets.value]
    const [widget] = nextWidgets.splice(index, 1)
    nextWidgets.splice(index - 1, 0, widget)
    widgets.value = nextWidgets
    saveLayout()
  }

  function moveWidgetDown(id: AdminDashboardWidgetId) {
    const index = widgets.value.findIndex(widget => widget.id === id)
    if (index === -1 || index >= widgets.value.length - 1) return
    const nextWidgets = [...widgets.value]
    const [widget] = nextWidgets.splice(index, 1)
    nextWidgets.splice(index + 1, 0, widget)
    widgets.value = nextWidgets
    saveLayout()
  }

  function setWidgetWidth(id: AdminDashboardWidgetId, width: AdminDashboardWidgetWidth) {
    const widget = widgets.value.find(item => item.id === id)
    if (!widget) return
    widget.width = width
    saveLayout()
  }

  return {
    widgets,
    visibleWidgets,
    loadLayout,
    saveLayout,
    resetLayout,
    toggleWidget,
    moveWidgetUp,
    moveWidgetDown,
    setWidgetWidth,
  }
})

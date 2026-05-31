import type { LocationQueryValue } from 'vue-router'
import type { StudentCardState } from '@/router/meta'

export interface StudentNavCard {
  title: string
  description: string
  status: string
  destination: string
  state: StudentCardState
  accent: 'indigo' | 'gold' | 'mint' | 'rose' | 'slate'
}

export function stateLabel(state: StudentCardState): string {
  switch (state) {
    case 'recommended':
      return '推荐入口'
    case 'resume':
      return '继续进行'
    case 'locked':
      return '需要登录'
    case 'attention':
      return '优先处理'
    case 'completed':
      return '已完成'
    default:
      return '自由进入'
  }
}

export function normalizeRedirectTarget(
  value: LocationQueryValue | LocationQueryValue[] | undefined,
  fallback = '/',
): string {
  if (Array.isArray(value)) {
    return typeof value[0] === 'string' && value[0] ? value[0] : fallback
  }
  return typeof value === 'string' && value ? value : fallback
}

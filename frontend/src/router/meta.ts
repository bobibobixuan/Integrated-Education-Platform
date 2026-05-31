import 'vue-router'

export type StudentCardState =
  | 'default'
  | 'recommended'
  | 'resume'
  | 'locked'
  | 'attention'
  | 'completed'

declare module 'vue-router' {
  interface RouteMeta {
    title?: string
    requiresAuth?: boolean
    backTo?: string
  }
}

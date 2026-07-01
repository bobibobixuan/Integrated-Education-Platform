<script setup lang="ts">
import { computed } from 'vue'

interface Point {
  label: string
  value: number
}

const props = withDefaults(defineProps<{
  points: Point[]
  color?: string
  fill?: string
  ariaLabel?: string
}>(), {
  color: '#1E40AF',
  fill: 'rgba(59, 130, 246, 0.18)',
  ariaLabel: '趋势图',
})

const width = 320
const height = 164
const paddingX = 18
const paddingY = 18

const maxValue = computed(() => {
  if (!props.points.length) return 1
  return Math.max(...props.points.map(point => point.value), 1)
})

const minValue = computed(() => {
  if (!props.points.length) return 0
  return Math.min(...props.points.map(point => point.value), 0)
})

const pointsString = computed(() => {
  if (!props.points.length) return ''
  const range = Math.max(maxValue.value - minValue.value, 1)
  return props.points.map((point, index) => {
    const x = props.points.length === 1
      ? width / 2
      : paddingX + ((width - paddingX * 2) * index) / (props.points.length - 1)
    const y = height - paddingY - ((point.value - minValue.value) / range) * (height - paddingY * 2)
    return `${x},${y}`
  }).join(' ')
})

const areaPath = computed(() => {
  if (!pointsString.value) return ''
  const points = pointsString.value.split(' ')
  const first = points[0]?.split(',')[0] ?? String(paddingX)
  const last = points[points.length - 1]?.split(',')[0] ?? String(width - paddingX)
  return `M ${first} ${height - paddingY} L ${points.join(' L ')} L ${last} ${height - paddingY} Z`
})

const latestPoint = computed(() => props.points[props.points.length - 1] ?? null)
</script>

<template>
  <div class="mini-line-chart">
    <div v-if="props.points.length === 0" class="mini-line-chart__empty">暂无趋势数据</div>
    <svg
      v-else
      class="mini-line-chart__svg"
      :viewBox="`0 0 ${width} ${height}`"
      role="img"
      :aria-label="props.ariaLabel"
    >
      <g class="mini-line-chart__grid">
        <line x1="18" y1="22" x2="302" y2="22" />
        <line x1="18" y1="82" x2="302" y2="82" />
        <line x1="18" y1="146" x2="302" y2="146" />
      </g>
      <path :d="areaPath" :fill="props.fill" />
      <polyline :points="pointsString" :stroke="props.color" fill="none" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" />
      <circle
        v-if="latestPoint"
        :cx="pointsString.split(' ').slice(-1)[0]?.split(',')[0]"
        :cy="pointsString.split(' ').slice(-1)[0]?.split(',')[1]"
        r="5"
        :fill="props.color"
      />
    </svg>
    <div v-if="props.points.length > 1" class="mini-line-chart__labels">
      <span>{{ props.points[0]?.label }}</span>
      <span>{{ latestPoint?.label }}</span>
    </div>
  </div>
</template>

<style scoped>
.mini-line-chart {
  display: grid;
  gap: 10px;
}

.mini-line-chart__svg {
  width: 100%;
  height: auto;
}

.mini-line-chart__grid line {
  stroke: rgba(148, 163, 184, 0.38);
  stroke-width: 1;
}

.mini-line-chart__labels {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  color: var(--admin-muted, #64748b);
  font-size: 12px;
}

.mini-line-chart__empty {
  min-height: 164px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  border: 1px dashed #cbd5e1;
  color: var(--admin-muted, #64748b);
  background: var(--admin-surface-soft, #f8fafc);
}
</style>

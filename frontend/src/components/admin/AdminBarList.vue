<script setup lang="ts">
import { computed } from 'vue'

type Tone = 'blue' | 'amber' | 'red' | 'green'

interface BarItem {
  label: string
  value: number
  hint?: string
  tone?: Tone
}

const props = defineProps<{
  items: BarItem[]
  suffix?: string
  emptyCopy?: string
}>()

const maxValue = computed(() => {
  if (!props.items.length) return 1
  return Math.max(...props.items.map(item => item.value), 1)
})

function barWidth(value: number) {
  return `${Math.max((value / maxValue.value) * 100, 6)}%`
}
</script>

<template>
  <div v-if="props.items.length === 0" class="bar-list__empty">{{ props.emptyCopy || '暂无数据' }}</div>
  <div v-else class="bar-list">
    <article v-for="item in props.items" :key="item.label" class="bar-list__item">
      <div class="bar-list__head">
        <strong>{{ item.label }}</strong>
        <span>{{ item.value }}{{ props.suffix || '' }}</span>
      </div>
      <div class="bar-list__track" aria-hidden="true">
        <div class="bar-list__fill" :class="`is-${item.tone || 'blue'}`" :style="{ width: barWidth(item.value) }" />
      </div>
      <p v-if="item.hint" class="bar-list__hint">{{ item.hint }}</p>
    </article>
  </div>
</template>

<style scoped>
.bar-list {
  display: grid;
  gap: 14px;
}

.bar-list__item {
  display: grid;
  gap: 8px;
}

.bar-list__head {
  display: flex;
  justify-content: space-between;
  gap: 14px;
  align-items: center;
}

.bar-list__head strong {
  color: var(--admin-text, #0f172a);
  font-size: 13px;
  font-weight: 700;
}

.bar-list__head span,
.bar-list__hint {
  color: var(--admin-muted, #64748b);
  font-size: 12px;
}

.bar-list__track {
  overflow: hidden;
  height: 10px;
  border-radius: 999px;
  background: #e8eef7;
}

.bar-list__fill {
  height: 100%;
  border-radius: inherit;
}

.bar-list__fill.is-blue {
  background: #2563eb;
}

.bar-list__fill.is-amber {
  background: #f59e0b;
}

.bar-list__fill.is-red {
  background: #ef4444;
}

.bar-list__fill.is-green {
  background: #16a34a;
}

.bar-list__empty {
  min-height: 140px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  border: 1px dashed #cbd5e1;
  color: var(--admin-muted, #64748b);
  background: var(--admin-surface-soft, #f8fafc);
}
</style>

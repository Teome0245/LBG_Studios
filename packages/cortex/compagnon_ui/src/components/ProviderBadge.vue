<template>
  <span
    class="inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-medium"
    :class="statusClasses"
  >
    <span class="h-1.5 w-1.5 rounded-full" :class="dotClasses" />
    <span>{{ name }}</span>
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  name: { type: String, required: true },
  status: { type: String, default: 'up' }, // 'up' | 'down' | 'degraded'
})

const statusClasses = computed(() => {
  if (props.status === 'up') return 'border-emerald-500/40 bg-emerald-500/10 text-emerald-300'
  if (props.status === 'degraded') return 'border-amber-500/40 bg-amber-500/10 text-amber-300'
  return 'border-rose-500/40 bg-rose-500/10 text-rose-300'
})

const dotClasses = computed(() => {
  if (props.status === 'up') return 'bg-emerald-400'
  if (props.status === 'degraded') return 'bg-amber-400'
  return 'bg-rose-400'
})
</script>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: { type: String, default: 'all' },
  counts: {
    type: Object,
    default: () => ({ moi: 0, ai: 0, timeline: 0 }),
  },
})

const emit = defineEmits(['update:modelValue'])

const crumbs = computed(() => [
  { id: 'all', label: 'Tout', count: null },
  { id: 'moi', label: 'Utilisateur', count: props.counts.moi },
  { id: 'ai', label: 'AI', count: props.counts.ai },
  { id: 'timeline', label: 'Timeline', count: props.counts.timeline },
])

function select(id) {
  emit('update:modelValue', id)
}
</script>

<template>
  <nav
    class="sticky top-0 z-[5] -mx-2 mb-4 px-2 py-2 bg-slate-950/80 backdrop-blur-md border-b border-white/5"
    aria-label="Filtre conversation"
  >
    <ol class="flex flex-wrap items-center gap-1 text-[11px] font-semibold tracking-wide uppercase">
      <template v-for="(c, i) in crumbs" :key="c.id">
        <li v-if="i > 0" class="text-slate-600 px-0.5 select-none" aria-hidden="true">/</li>
        <li>
          <button
            type="button"
            class="inline-flex items-center gap-1 px-2 py-1 rounded-lg transition-colors"
            :class="
              modelValue === c.id
                ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-white/5 border border-transparent'
            "
            :aria-current="modelValue === c.id ? 'true' : undefined"
            @click="select(c.id)"
          >
            {{ c.label }}
            <span
              v-if="c.count != null"
              class="font-mono text-[9px] opacity-60 normal-case tracking-normal"
            >{{ c.count }}</span>
          </button>
        </li>
      </template>
    </ol>
  </nav>
</template>

<script setup>
/**
 * A1 — Journal de contexte injecté (replié par défaut).
 * Montre pourquoi le Compagnon « sait » X — sans secrets.
 */
import { computed } from 'vue'

const props = defineProps({
  journal: { type: Object, default: null },
  openByDefault: { type: Boolean, default: false },
})

const blocks = computed(() => {
  const list = props.journal?.blocks
  return Array.isArray(list) ? list : []
})

const count = computed(() => {
  if (typeof props.journal?.count === 'number') return props.journal.count
  return blocks.value.length
})

const totalChars = computed(() => {
  if (typeof props.journal?.total_chars === 'number') return props.journal.total_chars
  return blocks.value.reduce((n, b) => n + (Number(b?.chars) || 0), 0)
})

const isEmpty = computed(() => count.value === 0 || !!props.journal?.empty)
</script>

<template>
  <details
    v-if="journal"
    class="mb-3.5 pb-3.5 border-b border-white/10 group/cj text-[11px] text-slate-400"
    :open="openByDefault ? true : undefined"
  >
    <summary
      class="cursor-pointer select-none list-none inline-flex items-center gap-1.5 hover:text-slate-300 [&::-webkit-details-marker]:hidden text-[10px] uppercase tracking-widest font-bold text-slate-400"
    >
      <span class="opacity-70 group-open/cj:rotate-90 transition-transform inline-block">›</span>
      Contexte ce tour
      <span class="font-mono text-[9px] opacity-60 normal-case tracking-normal">
        <template v-if="isEmpty">aucun</template>
        <template v-else>{{ count }} · {{ totalChars }}c</template>
      </span>
    </summary>
    <ul v-if="!isEmpty" class="mt-1.5 space-y-1 pl-1 border-l border-white/10">
      <li
        v-for="(b, i) in blocks"
        :key="`${b.id}-${i}`"
        class="flex flex-wrap items-baseline gap-x-2 gap-y-0.5"
      >
        <span class="font-mono text-[10px] text-cyan-300/80 shrink-0">{{ b.label || b.id }}</span>
        <span v-if="b.summary || b.detail" class="text-slate-500 truncate max-w-[14rem]">{{ b.summary || b.detail }}</span>
        <span v-if="b.chars" class="font-mono text-[9px] text-slate-600">{{ b.chars }}c</span>
      </li>
    </ul>
    <p v-else class="mt-1.5 text-xs text-slate-500 normal-case tracking-normal font-normal">
      Aucun bloc injecté ce tour (réponse courte ou sans couche Character).
    </p>
  </details>
</template>

<script setup>
import { useActivity } from '@/composables/useActivity'

const { current, toggleActivityOpen, clearActivity } = useActivity()

function lineClass(level) {
  if (level === 'ok') return 'text-emerald-400'
  if (level === 'warn') return 'text-amber-300'
  if (level === 'err') return 'text-rose-400'
  return 'text-slate-400'
}
</script>

<template>
  <div
    v-if="current"
    class="activity-encart mt-3 mb-1 max-w-xl"
    :data-phase="current.phase"
  >
    <button
      type="button"
      class="flex items-center gap-2 w-full text-left py-0.5 bg-transparent border-0 text-slate-300 cursor-pointer text-[13px]"
      @click="toggleActivityOpen"
    >
      <span
        class="text-slate-500 text-[11px] transition-transform"
        :class="{ '-rotate-90': !current.open }"
      >▾</span>
      <span class="font-semibold text-slate-100 truncate">{{ current.title }}</span>
      <span
        v-for="t in current.tools"
        :key="t"
        class="text-[10px] font-mono text-slate-500 border border-white/10 rounded px-1.5 py-px"
      >{{ t }}</span>
      <span class="flex-1" />
      <button
        type="button"
        class="border-0 bg-transparent text-slate-500 hover:text-slate-300 cursor-pointer px-1"
        title="Masquer"
        @click.stop="clearActivity"
      >···</button>
    </button>

    <div
      v-if="current.open"
      class="mt-1 rounded-xl border border-white/10 bg-slate-950/70 px-3 py-2 max-h-36 overflow-auto"
    >
      <pre class="m-0 font-mono text-[11px] leading-snug whitespace-pre-wrap break-words"><code
        v-for="(line, i) in current.lines"
        :key="i"
        :class="lineClass(line.level)"
      >{{ line.text }}{{ '\n' }}</code></pre>
    </div>

    <p
      class="mt-1.5 mb-0 text-[12px] flex items-center gap-2"
      :class="{
        'text-slate-400': current.phase === 'running' || current.phase === 'planning',
        'text-emerald-400': current.phase === 'done',
        'text-rose-400': current.phase === 'error',
      }"
    >
      <span
        v-if="current.phase === 'running' || current.phase === 'planning'"
        class="inline-block w-1.5 h-1.5 rounded-full bg-sky-400 animate-pulse"
      />
      {{ current.phaseLabel }}
    </p>
  </div>
</template>

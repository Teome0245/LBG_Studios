<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { apiUrl } from '@/api/http'
import ThemeToggle from './ThemeToggle.vue'
import { useLayout } from '../composables/useLayout'
import { PILOT_LINKS } from '../lib/pilotLinks.js'

const {
  histCollapsed,
  infraCollapsed,
  monitorCollapsed,
  opsMetricsVisible,
  toggleHist,
  toggleInfra,
  toggleMonitor,
  toggleOpsMetrics,
} = useLayout()

const deployEnv = (import.meta.env.VITE_DEPLOY_ENV || 'dev').toLowerCase()
const envLabel = (import.meta.env.VITE_ENV_LABEL || '').trim() || deployEnv.toUpperCase()
const isProd = deployEnv === 'prod' || deployEnv === 'production'

const cpuUsage = ref(null)
const memUsagePct = ref(null)
const memUsedMb = ref(null)
const memTotalMb = ref(null)

const activeAgent = ref('Compagnon')

function formatRamGiB(mb) {
  if (mb == null || typeof mb !== 'number') return ''
  return `${(mb / 1024).toFixed(1)} Go`
}

async function refreshMetrics() {
  if (!opsMetricsVisible.value) return
  try {
    const r = await fetch(apiUrl('/metrics'))
    if (!r.ok) return
    const data = await r.json()
    const sys = data?.system
    const cpu = sys?.cpu_usage_pct
    if (typeof cpu === 'number') cpuUsage.value = Math.round(cpu)
    const mp = sys?.memory_usage_pct
    if (typeof mp === 'number') memUsagePct.value = Math.round(mp)
    else memUsagePct.value = null
    const mu = sys?.memory_used_mb
    const mt = sys?.memory_total_mb
    memUsedMb.value = typeof mu === 'number' ? mu : null
    memTotalMb.value = typeof mt === 'number' ? mt : null
  } catch {
    /* best-effort */
  }
}

let intervalId
onMounted(() => {
  refreshMetrics()
  intervalId = setInterval(refreshMetrics, 2000)
})
onUnmounted(() => {
  if (intervalId) clearInterval(intervalId)
})
</script>

<template>
  <header class="h-16 border-b border-white/5 bg-slate-950/20 backdrop-blur-md flex items-center justify-between px-4 sm:px-6 z-10">
    <div class="flex items-center gap-3 sm:gap-4 min-w-0">
      <div class="flex flex-col min-w-0">
        <h2 class="text-sm font-bold font-outfit text-white leading-tight truncate">
          {{ activeAgent }}
        </h2>
        <div class="flex items-center gap-1.5">
          <span class="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
          <span class="text-[10px] text-emerald-500 font-bold tracking-widest uppercase">En ligne</span>
        </div>
      </div>
      <span
        class="hidden sm:inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-bold tracking-widest uppercase shrink-0"
        :class="isProd ? 'border-rose-500/40 bg-rose-500/10 text-rose-200' : 'border-sky-500/40 bg-sky-500/10 text-sky-200'"
      >
        {{ envLabel }}
      </span>
    </div>

    <div class="flex items-center gap-2 sm:gap-3">
      <a
        :href="PILOT_LINKS.home"
        target="_blank"
        rel="noopener noreferrer"
        class="hidden sm:inline-flex px-2.5 py-1 rounded-lg text-[10px] font-bold uppercase tracking-wide text-slate-400 hover:text-teal-200 hover:bg-teal-500/10 border border-white/10 hover:border-teal-500/30"
        title="Pilot · studio ops (Team, Jobs, Desktop)"
      >Pilot</a>

      <template v-if="opsMetricsVisible">
        <div class="hidden md:flex items-center gap-3">
          <div class="flex items-center gap-3 bg-white/5 px-3 py-1.5 rounded-full border border-white/5">
            <div class="flex flex-col items-end min-w-[3.25rem]">
              <span class="text-[9px] text-slate-500 font-bold uppercase tracking-tighter">CPU</span>
              <span class="text-xs font-mono text-white leading-none">
                {{ cpuUsage === null ? '—' : cpuUsage + '%' }}
              </span>
            </div>
            <div class="w-14 h-1.5 bg-slate-800 rounded-full overflow-hidden">
              <div class="h-full bg-emerald-500 transition-all duration-1000" :style="{ width: (cpuUsage ?? 0) + '%' }"></div>
            </div>
          </div>
          <div class="flex items-center gap-3 bg-white/5 px-3 py-1.5 rounded-full border border-white/5">
            <div class="flex flex-col items-end min-w-[3.25rem]">
              <span class="text-[9px] text-slate-500 font-bold uppercase tracking-tighter">Mémoire</span>
              <span class="text-xs font-mono text-white leading-none">
                {{ memUsagePct === null ? '—' : memUsagePct + '%' }}
              </span>
              <span
                v-if="memUsedMb != null && memTotalMb != null"
                class="text-[8px] font-mono text-slate-500 leading-tight mt-0.5 max-w-[5.5rem] truncate text-right"
              >
                {{ formatRamGiB(memUsedMb) }} / {{ formatRamGiB(memTotalMb) }}
              </span>
            </div>
            <div class="w-14 h-1.5 bg-slate-800 rounded-full overflow-hidden">
              <div class="h-full bg-sky-500 transition-all duration-1000" :style="{ width: (memUsagePct ?? 0) + '%' }"></div>
            </div>
          </div>
        </div>
      </template>

      <div class="flex items-center gap-0.5 sm:gap-1">
        <button
          type="button"
          class="hidden sm:inline-flex p-2 rounded-lg text-slate-400 hover:text-white hover:bg-white/5"
          :title="opsMetricsVisible ? 'Masquer métriques' : 'Afficher CPU / RAM'"
          @click="toggleOpsMetrics"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        </button>
        <button
          type="button"
          class="hidden sm:inline-flex p-2 rounded-lg text-slate-400 hover:text-white hover:bg-white/5"
          :title="histCollapsed ? 'Discussions' : 'Masquer discussions'"
          @click="toggleHist"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h10M4 18h16" />
          </svg>
        </button>
        <button
          type="button"
          class="inline-flex p-2 rounded-lg text-slate-400 hover:text-white hover:bg-white/5"
          :title="infraCollapsed ? 'Infra LAN' : 'Masquer infra'"
          @click="toggleInfra"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
          </svg>
        </button>
        <button
          type="button"
          class="inline-flex p-2 rounded-lg text-slate-400 hover:text-white hover:bg-white/5"
          :title="monitorCollapsed ? 'Monitoring' : 'Masquer monitoring'"
          @click="toggleMonitor"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 10a2 2 0 002 2h2a2 2 0 002-2V7a2 2 0 00-2-2h-2a2 2 0 00-2 2" />
          </svg>
        </button>
        <ThemeToggle />
      </div>
    </div>
  </header>
</template>

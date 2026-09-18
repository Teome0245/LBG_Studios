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
  <header class="h-16 border-b border-white/5 bg-slate-950/40 backdrop-blur-xl flex items-center justify-between px-4 sm:px-6 z-10 transition-colors">
    <div class="flex items-center gap-3 sm:gap-4 min-w-0">
      <div class="h-9 w-9 rounded-xl bg-gradient-to-tr from-emerald-600/30 to-teal-500/20 border border-emerald-500/30 flex items-center justify-center shrink-0 shadow-lg shadow-emerald-950/40">
        <span class="font-outfit font-black text-emerald-400 text-base leading-none">C</span>
      </div>

      <div class="flex flex-col min-w-0">
        <div class="flex items-center gap-2">
          <h2 class="text-base font-bold font-outfit text-slate-100 tracking-tight leading-tight truncate">
            {{ activeAgent }}
          </h2>
          <span
            class="hidden sm:inline-flex items-center rounded-md border px-1.5 py-0.5 text-[9px] font-bold tracking-widest uppercase shrink-0"
            :class="isProd ? 'border-rose-500/30 bg-rose-500/10 text-rose-300' : 'border-slate-700 bg-slate-800/60 text-slate-300'"
          >
            {{ envLabel }}
          </span>
        </div>
        <div class="flex items-center gap-1.5 mt-0.5">
          <span class="h-2 w-2 rounded-full bg-emerald-400 animate-pulse-soft"></span>
          <span class="text-[10px] text-emerald-400/90 font-medium tracking-wide">Présent · Prêt à agir</span>
        </div>
      </div>
    </div>

    <div class="flex items-center gap-2 sm:gap-3">
      <a
        :href="PILOT_LINKS.home"
        target="_blank"
        rel="noopener noreferrer"
        class="hidden sm:inline-flex items-center gap-1 px-3 py-1.5 rounded-xl text-[11px] font-semibold tracking-wide text-slate-300 hover:text-white bg-white/5 hover:bg-teal-500/15 border border-white/10 hover:border-teal-500/40 transition-all duration-200 shadow-sm"
        title="Pilot · cockpit ops (Team, Jobs, Desktop)"
      >
        <span>Pilot Ops</span>
        <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3 opacity-60" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
        </svg>
      </a>

      <!-- Métriques CPU/RAM repliées par défaut sous toggle -->
      <template v-if="opsMetricsVisible">
        <div class="hidden md:flex items-center gap-2.5 bg-slate-900/80 px-3 py-1.5 rounded-xl border border-white/10 text-xs">
          <div class="flex items-center gap-2">
            <span class="text-[9px] text-slate-400 font-bold uppercase tracking-wider">CPU</span>
            <span class="font-mono text-slate-200">{{ cpuUsage === null ? '—' : cpuUsage + '%' }}</span>
            <div class="w-10 h-1 bg-slate-800 rounded-full overflow-hidden">
              <div class="h-full bg-emerald-400 transition-all duration-700" :style="{ width: (cpuUsage ?? 0) + '%' }"></div>
            </div>
          </div>
          <div class="h-3 w-[1px] bg-white/10 mx-0.5"></div>
          <div class="flex items-center gap-2">
            <span class="text-[9px] text-slate-400 font-bold uppercase tracking-wider">RAM</span>
            <span class="font-mono text-slate-200">{{ memUsagePct === null ? '—' : memUsagePct + '%' }}</span>
            <div class="w-10 h-1 bg-slate-800 rounded-full overflow-hidden">
              <div class="h-full bg-sky-400 transition-all duration-700" :style="{ width: (memUsagePct ?? 0) + '%' }"></div>
            </div>
          </div>
        </div>
      </template>

      <div class="flex items-center gap-1 sm:gap-1.5">
        <button
          type="button"
          class="hidden sm:inline-flex p-2 rounded-xl text-slate-400 hover:text-slate-100 hover:bg-white/5 transition-colors"
          :class="opsMetricsVisible ? 'text-teal-300 bg-teal-500/10 border border-teal-500/20' : 'border border-transparent'"
          :title="opsMetricsVisible ? 'Masquer métriques' : 'Afficher CPU / RAM'"
          @click="toggleOpsMetrics"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        </button>
        <button
          type="button"
          class="hidden sm:inline-flex p-2 rounded-xl text-slate-400 hover:text-slate-100 hover:bg-white/5 transition-colors border border-transparent"
          :title="histCollapsed ? 'Discussions' : 'Masquer discussions'"
          @click="toggleHist"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h10M4 18h16" />
          </svg>
        </button>
        <button
          type="button"
          class="inline-flex p-2 rounded-xl text-slate-400 hover:text-slate-100 hover:bg-white/5 transition-colors"
          :class="!infraCollapsed ? 'text-teal-300 bg-teal-500/10 border border-teal-500/20' : 'border border-transparent'"
          :title="infraCollapsed ? 'Infra LAN' : 'Masquer infra'"
          @click="toggleInfra"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
          </svg>
        </button>
        <button
          type="button"
          class="inline-flex p-2 rounded-xl text-slate-400 hover:text-slate-100 hover:bg-white/5 transition-colors"
          :class="!monitorCollapsed ? 'text-teal-300 bg-teal-500/10 border border-teal-500/20' : 'border border-transparent'"
          :title="monitorCollapsed ? 'Monitoring' : 'Masquer monitoring'"
          @click="toggleMonitor"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 10a2 2 0 002 2h2a2 2 0 002-2V7a2 2 0 00-2-2h-2a2 2 0 00-2 2" />
          </svg>
        </button>
        <ThemeToggle />
      </div>
    </div>
  </header>
</template>

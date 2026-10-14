<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { apiUrl } from '@/api/http'
import ThemeToggle from './ThemeToggle.vue'
import { useLayout } from '../composables/useLayout'
import { useInitiative } from '../composables/useInitiative'
import { PILOT_LINKS } from '../lib/pilotLinks.js'
import { isTtsEnabled, setTtsEnabled, fetchTtsHealth, stopTts } from '@/lib/tts'

const {
  histCollapsed,
  infraCollapsed,
  monitorCollapsed,
  agentsLiveCollapsed,
  opsMetricsVisible,
  characterPanelOpen,
  toggleHist,
  toggleInfra,
  toggleMonitor,
  toggleAgentsLive,
  toggleOpsMetrics,
  toggleCharacterPanel,
} = useLayout()

const { selfLine, lastSelf } = useInitiative()

const deployEnv = (import.meta.env.VITE_DEPLOY_ENV || 'dev').toLowerCase()
const envLabel = (import.meta.env.VITE_ENV_LABEL || '').trim() || deployEnv.toUpperCase()
const isProd = deployEnv === 'prod' || deployEnv === 'production'

const cpuUsage = ref(null)
const memUsagePct = ref(null)
const memUsedMb = ref(null)
const memTotalMb = ref(null)

const activeAgent = ref('Compagnon')
const ttsOn = ref(false)
const ttsReady = ref(false)

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

function toggleTts() {
  const next = !ttsOn.value
  setTtsEnabled(next)
  ttsOn.value = next
  if (!next) stopTts()
}

let intervalId
onMounted(() => {
  ttsOn.value = isTtsEnabled()
  refreshMetrics()
  intervalId = setInterval(refreshMetrics, 2000)
  void fetchTtsHealth().then((h) => {
    ttsReady.value = Boolean(h?.ok)
  })
})
onUnmounted(() => {
  if (intervalId) clearInterval(intervalId)
})
</script>

<template>
  <header class="border-b border-white/5 bg-slate-950/40 backdrop-blur-xl z-10 transition-colors">
    <div class="h-14 sm:h-16 flex items-center justify-between px-4 sm:px-6">
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
            <span
              v-if="memUsedMb != null && memTotalMb != null"
              class="hidden xl:inline text-[9px] text-slate-500 font-mono"
            >{{ formatRamGiB(memUsedMb) }}/{{ formatRamGiB(memTotalMb) }}</span>
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
            class="inline-flex items-center gap-1 px-2 py-1.5 rounded-xl text-slate-400 hover:text-slate-100 hover:bg-white/5 transition-colors"
            :class="!agentsLiveCollapsed ? 'text-teal-300 bg-teal-500/10 border border-teal-500/20' : 'border border-transparent'"
            :title="agentsLiveCollapsed ? 'Agents live (fleet)' : 'Masquer agents live'"
            @click="toggleAgentsLive"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
            <span class="hidden md:inline text-[10px] font-bold tracking-wide uppercase">Agents</span>
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
            class="inline-flex items-center gap-1 px-2 py-1.5 rounded-xl text-slate-400 hover:text-slate-100 hover:bg-white/5 transition-colors"
            :class="ttsOn ? 'text-teal-300 bg-teal-500/10 border border-teal-500/20' : 'border border-transparent'"
            :title="ttsOn ? (ttsReady ? 'Couper la voix (TTS LAN)' : 'Voix activée — Piper hors ligne') : 'Activer la voix (TTS LAN Piper)'"
            @click="toggleTts"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                v-if="ttsOn"
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M15.536 8.464a5 5 0 010 7.072M12 6v12m0 0l-4-4H5a1 1 0 01-1-1v-2a1 1 0 011-1h3l4-4zM18.364 5.636a9 9 0 010 12.728"
              />
              <path
                v-else
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707A1 1 0 0112 5v14a1 1 0 01-1.707.707L5.586 15zM17 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2"
              />
            </svg>
            <span class="hidden md:inline text-[10px] font-bold tracking-wide uppercase">Voix</span>
          </button>
          <button
            type="button"
            class="inline-flex items-center gap-1 px-2 py-1.5 rounded-xl text-slate-400 hover:text-slate-100 hover:bg-white/5 transition-colors"
            :class="characterPanelOpen ? 'text-teal-300 bg-teal-500/10 border border-teal-500/20' : 'border border-transparent'"
            :title="characterPanelOpen ? 'Masquer caractère' : 'Caractère (7 dials lab)'"
            @click="toggleCharacterPanel"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
            </svg>
            <span class="hidden md:inline text-[10px] font-bold tracking-wide uppercase">Caract.</span>
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
    </div>

    <!-- Self Cortex : sous le header (plus de pastille flottante au-dessus du chat) -->
    <div
      v-if="selfLine"
      class="px-4 sm:px-6 pb-2"
      :title="lastSelf?.enabled ? 'Self-State Agency' : 'Self'"
      role="status"
    >
      <div class="flex items-center gap-2 max-w-3xl min-w-0 px-2.5 py-1 rounded-lg border border-slate-700/60 bg-slate-900/50">
        <span class="h-1.5 w-1.5 rounded-full bg-teal-400 shrink-0 shadow-[0_0_6px_rgba(45,212,191,0.55)]" aria-hidden="true" />
        <span class="text-[9px] font-bold uppercase tracking-wider text-teal-300/90 shrink-0">Self</span>
        <span class="text-[10px] text-slate-400 truncate">{{ selfLine }}</span>
      </div>
    </div>
  </header>
</template>

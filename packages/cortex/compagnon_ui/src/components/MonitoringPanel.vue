<template>
  <div class="h-full flex flex-col">

    <header class="px-4 py-2 border-b border-slate-800 bg-slate-900/40 backdrop-blur flex items-center justify-between">
      <h2 class="text-xs font-semibold tracking-wide uppercase text-slate-300">
        Monitoring
      </h2>
      <button
        type="button"
        class="p-1 rounded text-slate-500 hover:text-white"
        title="Masquer"
        @click="toggleMonitor"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 5l7 7-7 7M5 5l7 7-7 7" />
        </svg>
      </button>
    </header>

    <div class="flex-1 px-4 py-3 space-y-4 text-xs overflow-y-auto scrollbar-custom">

      <!-- Lyra en haut de colonne -->
      <LyraPanel />

      <!-- Statut Backend -->
      <div class="flex items-center gap-2">
        <span
          class="h-2 w-2 rounded-full flex-shrink-0"
          :class="backendOnline ? 'bg-emerald-400 animate-pulse' : 'bg-red-500'"
        ></span>
        <span class="opacity-70">Backend</span>
        <span class="ml-auto font-semibold" :class="backendOnline ? 'text-emerald-300' : 'text-red-400'">
          {{ backendOnline ? 'En ligne' : 'Hors ligne' }}
        </span>
      </div>

      <!-- Environnements Local / LAN / Prod -->
      <div v-if="envSurfaces.length">
        <h3 class="text-[11px] font-semibold uppercase mb-2 opacity-60 tracking-widest">
          Environnements
        </h3>
        <div class="flex flex-wrap gap-1.5">
          <div
            v-for="s in envSurfaces"
            :key="s.id"
            class="flex-1 min-w-[72px] rounded-lg border px-2 py-1.5 text-center transition-colors"
            :class="envBadgeClass(s)"
            :title="s.detail || s.subtitle"
          >
            <div class="text-[10px] font-bold uppercase tracking-wide">{{ s.label }}</div>
            <div class="text-[9px] opacity-70 truncate">{{ s.subtitle }}</div>
          </div>
        </div>
      </div>

      <!-- Roster Team en premier après Lyra — New Agent stub -->
      <div>
        <div class="flex items-center justify-between mb-2 gap-2">
          <h3 class="text-[11px] font-semibold uppercase opacity-60 tracking-widest">
            Équipe
          </h3>
          <RouterLink
            to="/agents/map"
            class="text-[10px] text-emerald-500/90 hover:text-emerald-400 font-medium shrink-0"
          >
            Carte →
          </RouterLink>
        </div>
        <div class="mb-3">
          <NewAgentStub />
        </div>
        <TeamRosterPanel />
      </div>

      <!-- Sondes HTTP (repliable) -->
      <details class="group">
        <summary class="cursor-pointer text-[11px] font-semibold uppercase opacity-60 tracking-widest list-none flex items-center gap-1.5">
          <span class="text-slate-500 group-open:rotate-90 transition-transform">▸</span>
          Sondes HTTP
          <span class="ml-auto text-[9px] font-mono font-normal normal-case tracking-normal opacity-50">
            {{ agentRows.length }}
          </span>
        </summary>
        <div class="space-y-1.5 mt-2">
          <div
            v-for="a in agentRows"
            :key="a.id"
            class="flex items-start gap-2 min-w-0"
          >
            <span
              class="h-1.5 w-1.5 rounded-full flex-shrink-0 mt-1"
              :class="statusDotClass(a.status)"
              :title="statusLabel(a.status)"
            />
            <div class="min-w-0 flex-1">
              <div class="flex items-center justify-between gap-2">
                <span class="opacity-90 truncate" :title="a.label">{{ a.label }}</span>
                <span class="text-[10px] font-semibold shrink-0" :class="statusTextClass(a.status)">
                  {{ statusLabel(a.status) }}
                </span>
              </div>
              <div class="text-[10px] text-slate-500 font-mono truncate" :title="a.base_url || ''">
                {{ a.base_url || '—' }}
              </div>
              <div v-if="a.latency_ms != null" class="text-[9px] text-slate-600 font-mono">
                {{ a.latency_ms }} ms
              </div>
            </div>
          </div>
          <div v-if="agentRows.length === 0" class="text-slate-500 italic text-[10px]">
            Aucun agent — sonde indisponible
          </div>
        </div>
      </details>

      <!-- Providers actifs -->
      <div>
        <h3 class="text-[11px] font-semibold uppercase mb-2 opacity-60 tracking-widest">
          Providers
        </h3>
        <div class="space-y-1.5">
          <div
            v-for="(data, provider) in providerStats"
            :key="provider"
            class="flex items-center justify-between"
          >
            <div class="flex items-center gap-2">
              <span
                class="h-1.5 w-1.5 rounded-full flex-shrink-0"
                :class="data.errors === 0 ? 'bg-emerald-400' : data.success === 0 ? 'bg-red-500' : 'bg-yellow-400'"
              ></span>
              <span class="capitalize opacity-80">{{ provider }}</span>
            </div>
            <div class="flex items-center gap-2 text-[10px] font-mono">
              <span class="text-emerald-400">✓{{ data.success }}</span>
              <span class="text-red-400">✗{{ data.errors }}</span>
              <span class="text-slate-400">{{ (data.latency * 1000).toFixed(0) }}ms</span>
            </div>
          </div>
          <div v-if="Object.keys(providerStats).length === 0" class="text-slate-500 italic text-[10px]">
            Aucune donnée — en attente de requêtes…
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { RouterLink } from 'vue-router'
import { http } from '@/api/http'
import LyraPanel from './LyraPanel.vue'
import TeamRosterPanel from './TeamRosterPanel.vue'
import NewAgentStub from './NewAgentStub.vue'
import { useLayout } from '../composables/useLayout'

const { toggleMonitor } = useLayout()

const backendOnline = ref(false)
const providerStats = ref({})
const agentRows = ref([])
const envSurfaces = ref([])
const envCurrent = ref('dev')

const STATUS_FR = {
  online: 'En ligne',
  reachable: 'Joignable',
  offline: 'Hors ligne',
  off: 'Éteint',
  local: 'Interne',
}

function statusLabel(key) {
  return STATUS_FR[key] || key || '—'
}

function statusDotClass(key) {
  if (key === 'online') return 'bg-emerald-400 shadow-sm shadow-emerald-500/30'
  if (key === 'reachable') return 'bg-amber-400 shadow-sm shadow-amber-500/20'
  if (key === 'offline') return 'bg-orange-500'
  if (key === 'off') return 'bg-slate-600'
  if (key === 'local') return 'bg-cyan-400'
  return 'bg-slate-500'
}

function statusTextClass(key) {
  if (key === 'online') return 'text-emerald-300'
  if (key === 'reachable') return 'text-amber-300'
  if (key === 'offline') return 'text-orange-400'
  if (key === 'off') return 'text-slate-500'
  if (key === 'local') return 'text-cyan-300'
  return 'text-slate-400'
}

function envBadgeClass(surface) {
  if (surface.active) {
    return 'border-emerald-500/40 bg-emerald-500/15 text-emerald-200 shadow-sm shadow-emerald-500/10'
  }
  return 'border-white/10 bg-white/5 text-slate-500'
}

async function loadHealth() {
  try {
    const res = await http.get('/health')
    backendOnline.value = true
    providerStats.value = res.data?.providers ?? {}
    envSurfaces.value = res.data?.env_surfaces?.surfaces ?? []
    envCurrent.value = res.data?.env_surfaces?.current ?? res.data?.env?.name ?? 'dev'
  } catch (e) {
    backendOnline.value = false
    providerStats.value = {}
    envSurfaces.value = []
  }
}

async function loadAgentsMonitor() {
  try {
    const res = await http.get('/monitor/agents', { params: { _t: Date.now() } })
    agentRows.value = Array.isArray(res.data?.agents) ? res.data.agents : []
  } catch (e) {
    agentRows.value = []
  }
}

async function tick() {
  await Promise.all([loadHealth(), loadAgentsMonitor()])
}

let intervalId
onMounted(() => {
  tick()
  intervalId = setInterval(tick, 5000)
})
onUnmounted(() => {
  if (intervalId) clearInterval(intervalId)
})
</script>

<style scoped>
:global(html.light) header {
  background: rgba(255,255,255,0.6);
  color: #0f172a;
}
:global(html.light) h3,
:global(html.light) h2 {
  color: #0f172a;
}
</style>

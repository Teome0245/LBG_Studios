<template>
  <div class="space-y-4">
    <div>
      <div class="flex items-center justify-between mb-2 gap-2">
        <h3 class="text-[11px] font-semibold uppercase opacity-60 tracking-widest">
          Infra LAN
        </h3>
        <span
          v-if="ok !== null"
          class="text-[9px] font-mono"
          :class="ok ? 'text-emerald-400' : 'text-orange-400'"
        >
          {{ ok ? 'P03' : 'KO' }}
        </span>
      </div>

      <div v-if="loading && !hosts.length" class="text-slate-500 italic text-[10px]">
        Chargement snapshot…
      </div>
      <div v-else-if="!hosts.length" class="text-slate-500 italic text-[10px]">
        Snapshot indisponible
      </div>

      <div v-else class="space-y-2">
        <button
          v-for="h in hosts"
          :key="h.host"
          type="button"
          class="w-full text-left rounded-lg border px-2 py-1.5 transition-colors"
          :class="hostCardClass(h)"
          :title="`${h.label} — ${h.host}`"
          @click="onHostClick(h)"
        >
          <div class="flex items-center justify-between gap-1 mb-1.5">
            <span class="text-[10px] font-semibold truncate">{{ h.label || h.host }}</span>
            <span class="text-[9px] font-mono opacity-70 shrink-0">{{ h.host }}</span>
          </div>
          <div class="space-y-1">
            <div class="flex items-center gap-2">
              <span class="text-[8px] uppercase tracking-wider text-slate-500 w-7 shrink-0">RAM</span>
              <div class="flex-1 h-1.5 rounded-full bg-slate-800 overflow-hidden">
                <div
                  class="h-full rounded-full transition-all duration-500"
                  :class="barClass(h.mem_used_pct, 85)"
                  :style="{ width: clampPct(h.mem_used_pct) + '%' }"
                />
              </div>
              <span class="text-[9px] font-mono text-slate-400 w-7 text-right">{{ h.mem_used_pct ?? '—' }}%</span>
            </div>
            <div class="flex items-center gap-2">
              <span class="text-[8px] uppercase tracking-wider text-slate-500 w-7 shrink-0">Disk</span>
              <div class="flex-1 h-1.5 rounded-full bg-slate-800 overflow-hidden">
                <div
                  class="h-full rounded-full transition-all duration-500"
                  :class="barClass(h.disk_used_pct, 90)"
                  :style="{ width: clampPct(h.disk_used_pct) + '%' }"
                />
              </div>
              <span class="text-[9px] font-mono text-slate-400 w-7 text-right">{{ h.disk_used_pct ?? '—' }}%</span>
            </div>
            <div v-if="h.load_avg" class="text-[9px] font-mono text-slate-500 truncate" :title="'load '+h.load_avg">
              Load {{ String(h.load_avg).split(' ')[0] }}
            </div>
          </div>
        </button>
      </div>
    </div>

    <!-- Dernière tâche + logs -->
    <div>
      <h3 class="text-[11px] font-semibold uppercase opacity-60 tracking-widest mb-2">
        Logs
      </h3>

      <div
        v-if="lastTask"
        class="rounded-lg border px-2 py-1.5 mb-2"
        :class="lastTask.ok ? 'border-emerald-500/25 bg-emerald-500/5' : 'border-white/10 bg-white/5'"
      >
        <div class="flex items-center justify-between gap-1 text-[9px] uppercase tracking-wider text-slate-500">
          <span>Dernière tâche</span>
          <span class="font-mono">{{ lastTask.age || '—' }}</span>
        </div>
        <p class="text-[10px] text-slate-200 mt-0.5 leading-snug">
          <span class="font-semibold" :class="statusColor(lastTask.status)">{{ lastTask.status }}</span>
          <span class="text-slate-500 mx-1">·</span>
          {{ lastTask.role }}
        </p>
        <p class="text-[10px] text-slate-400 truncate mt-0.5" :title="lastTask.objective">{{ lastTask.objective }}</p>
      </div>

      <div v-if="mission" class="text-[9px] text-slate-500 mb-2 font-mono truncate" :title="mission.objective">
        Mission {{ mission.status }} · {{ (mission.objective || '').slice(0, 48) }}…
      </div>

      <ul v-if="logs.length" class="space-y-1 max-h-36 overflow-y-auto scrollbar-custom">
        <li
          v-for="(log, i) in logs"
          :key="i"
          class="text-[10px] leading-snug border-l-2 pl-2 py-0.5"
          :class="logBorder(log)"
        >
          <div class="flex justify-between gap-1">
            <span class="font-mono text-[9px] uppercase" :class="statusColor(log.status)">{{ log.status || log.kind }}</span>
            <span class="text-slate-600 font-mono shrink-0">{{ log.age }}</span>
          </div>
          <p class="text-slate-400 truncate" :title="log.label">{{ log.label || log.detail }}</p>
        </li>
      </ul>
      <p v-else class="text-slate-500 italic text-[10px]">Aucune activité récente</p>
    </div>

    <!-- MMO Prime / Core3 -->
    <div>
      <h3 class="text-[11px] font-semibold uppercase opacity-60 tracking-widest mb-2">
        MMO
      </h3>
      <div class="space-y-2">
        <div class="rounded-lg border border-white/10 bg-white/5 px-2 py-1.5">
          <div class="flex items-center justify-between gap-1">
            <span class="text-[10px] font-semibold text-slate-200">246 Prime</span>
            <a
              v-if="prime?.dashboard_url"
              :href="prime.dashboard_url"
              target="_blank"
              rel="noreferrer"
              class="text-[9px] text-sky-400 hover:text-sky-300"
            >:8792 ↗</a>
          </div>
          <div class="flex items-center gap-1.5 mt-0.5 text-[10px]">
            <span :class="prime?.ok ? 'text-emerald-400' : 'text-red-400'">{{ prime?.ok ? '●' : '○' }}</span>
            <span class="text-slate-400">{{ prime?.online_count ?? 0 }} en ligne</span>
          </div>
          <p v-if="(prime?.players_online || []).length" class="text-[9px] text-slate-500 mt-0.5 truncate">
            {{ prime.players_online.join(', ') }}
          </p>
        </div>
        <div class="rounded-lg border border-white/10 bg-white/5 px-2 py-1.5">
          <div class="flex items-center justify-between gap-1">
            <span class="text-[10px] font-semibold text-slate-200">245 Core3</span>
            <a
              v-if="lab?.dashboard_url"
              :href="lab.dashboard_url"
              target="_blank"
              rel="noreferrer"
              class="text-[9px] text-sky-400 hover:text-sky-300"
            >:8792 ↗</a>
          </div>
          <p class="text-[9px] text-slate-500 mt-0.5 leading-snug">{{ lab?.note || 'origine SWG' }}</p>
          <div class="flex gap-3 mt-1 text-[9px] font-mono text-slate-400">
            <span>
              <span :class="lab?.swgemu?.running ? 'text-emerald-400' : 'text-slate-600'">●</span>
              swgemu
            </span>
            <span>
              <span :class="lab?.clean?.running ? 'text-emerald-400' : 'text-slate-600'">●</span>
              clean
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Sous-projets (actifs) -->
    <div v-if="subprojects.length">
      <h3 class="text-[11px] font-semibold uppercase opacity-60 tracking-widest mb-2">
        Sous-projets
        <span class="font-normal normal-case tracking-normal text-slate-600 ml-1">
          {{ subActive }} actifs
        </span>
      </h3>
      <div class="space-y-1 max-h-40 overflow-y-auto scrollbar-custom">
        <button
          v-for="sp in subprojects"
          :key="sp.id || sp.label"
          type="button"
          class="w-full text-left rounded-lg border border-white/10 bg-white/5 px-2 py-1.5 hover:border-violet-400/30 transition-colors"
          :class="sp.status === 'gelé' ? 'opacity-60 border-dashed' : ''"
          :title="sp.owner ? `Owner · ${sp.owner}` : sp.label"
          @click="onSubprojectClick(sp)"
        >
          <div class="flex items-center justify-between gap-1">
            <span class="text-[10px] font-semibold text-slate-200 truncate">{{ sp.label }}</span>
            <span class="text-[8px] uppercase tracking-wider shrink-0 px-1 rounded" :class="statusBadge(sp.status)">
              {{ sp.status_label || sp.status }}
            </span>
          </div>
          <p v-if="sp.owner" class="text-[9px] text-slate-500 truncate mt-0.5">{{ sp.owner }}</p>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import { http } from '@/api/http'

const emit = defineEmits(['ask'])

const hosts = ref([])
const ok = ref(null)
const loading = ref(false)
const lastTask = ref(null)
const logs = ref([])
const mission = ref(null)
const prime = ref(null)
const lab = ref(null)
const subprojects = ref([])
const subActive = ref(0)

function clampPct(v) {
  const n = Number(v)
  if (Number.isNaN(n)) return 0
  return Math.max(0, Math.min(100, n))
}

function barClass(pct, warnAt) {
  const n = Number(pct) || 0
  if (n >= warnAt) return 'bg-orange-400'
  if (n >= warnAt * 0.7) return 'bg-amber-400'
  return 'bg-emerald-400'
}

function hostCardClass(h) {
  if (h.ok === false) return 'border-red-500/30 bg-red-500/5 text-red-200'
  const mem = Number(h.mem_used_pct) || 0
  const disk = Number(h.disk_used_pct) || 0
  if (mem > 85 || disk > 90) return 'border-orange-500/30 bg-orange-500/5 text-orange-100'
  return 'border-white/10 bg-white/5 text-slate-300 hover:border-emerald-500/30'
}

function statusColor(st) {
  const s = String(st || '').toLowerCase()
  if (s === 'done' || s === 'success' || s === 'ok') return 'text-emerald-400'
  if (s === 'failed' || s === 'error') return 'text-red-400'
  if (s === 'running' || s === 'review') return 'text-amber-300'
  return 'text-slate-400'
}

function logBorder(log) {
  const s = String(log.status || '').toLowerCase()
  if (s === 'done' || log.ok) return 'border-emerald-500/40'
  if (s === 'failed') return 'border-red-500/40'
  if (s === 'running' || s === 'review') return 'border-amber-500/40'
  return 'border-white/15'
}

function onHostClick(h) {
  const label = h.label || h.host
  emit('ask', `diagnostic complet sur ${label} (${h.host})`)
}

function statusBadge(status) {
  const s = String(status || '')
  if (s === 'prod' || s === 'actif' || s === 'prod_parallèle') return 'bg-emerald-500/20 text-emerald-300'
  if (s === 'en_cours') return 'bg-sky-500/20 text-sky-300'
  if (s === 'transition') return 'bg-amber-500/20 text-amber-300'
  if (s === 'gelé') return 'bg-slate-500/20 text-slate-400'
  return 'bg-white/10 text-slate-400'
}

function ownerMention(sp) {
  if (sp?.persona === 'Pygmalion') return '@pygmalion'
  const role = sp?.owner_role
  if (role === 'ops') return '@hephaistos'
  if (role === 'pm') return '@themis'
  if (role === 'qa') return '@argus'
  if (role === 'player_ia') return '@choeur'
  if (role === 'dev_game' || role === 'dev_godot') return '@iris'
  return null
}

function onSubprojectClick(sp) {
  const m = ownerMention(sp)
  if (m) emit('ask', `${m} point sur ${sp.label || sp.id}`)
  else emit('ask', `team: status sous-projet ${sp.label || sp.id}`)
}

async function load() {
  loading.value = true
  try {
    const res = await http.get('/monitor/cockpit', { params: { _t: Date.now() } })
    ok.value = res.data?.ok !== false
    hosts.value = Array.isArray(res.data?.infra) ? res.data.infra : []
    const act = res.data?.activity || {}
    lastTask.value = act.last_task || null
    mission.value = act.mission || null
    const raw = Array.isArray(act.logs) ? act.logs : []
    logs.value = raw.filter((l) => l.kind === 'task' || l.kind === 'campus_report').slice(0, 8)
    const mmo = res.data?.mmo || {}
    prime.value = mmo.prime_246 || null
    lab.value = mmo.lab_245 || null
    const sp = res.data?.subprojects || {}
    const items = Array.isArray(sp.items) ? sp.items : []
    // Actifs d’abord, max 8
    const active = items.filter((i) => i.status !== 'gelé' && i.status !== 'etagere')
    const frozen = items.filter((i) => i.status === 'gelé' || i.status === 'etagere')
    subprojects.value = [...active, ...frozen].slice(0, 10)
    subActive.value = sp.counts?.active ?? active.length
  } catch {
    ok.value = false
    hosts.value = []
    lastTask.value = null
    logs.value = []
    mission.value = null
    prime.value = null
    lab.value = null
    subprojects.value = []
    subActive.value = 0
  } finally {
    loading.value = false
  }
}

let intervalId
onMounted(() => {
  load()
  intervalId = setInterval(load, 15000)
})
onUnmounted(() => {
  if (intervalId) clearInterval(intervalId)
})
</script>

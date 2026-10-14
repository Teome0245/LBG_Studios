<template>
  <div class="flex flex-col h-full min-h-0">
    <div class="flex items-center justify-between gap-2 px-3 py-2.5 border-b border-white/5 shrink-0">
      <div class="min-w-0">
        <h2 class="text-[11px] font-semibold uppercase tracking-widest text-slate-400">
          Agents live
        </h2>
        <p class="text-[9px] text-slate-600 mt-0.5 truncate">
          <template v-if="busyCount">{{ busyCount }} actif{{ busyCount > 1 ? 's' : '' }}</template>
          <template v-else>flotte idle</template>
          <span v-if="l2PendingCount" class="text-amber-400/90"> · L2 {{ l2PendingCount }}</span>
        </p>
      </div>
      <div class="flex items-center gap-1 shrink-0">
        <button
          type="button"
          class="p-1.5 rounded-lg text-slate-500 hover:text-slate-200 hover:bg-white/5 transition-colors"
          title="Rafraîchir"
          @click="refresh"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" :class="loading ? 'animate-spin' : ''" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </button>
        <button
          type="button"
          class="p-1.5 rounded-lg text-slate-500 hover:text-slate-200 hover:bg-white/5 transition-colors"
          title="Fermer"
          @click="toggleAgentsLive"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>

    <div class="flex-1 overflow-y-auto px-2.5 py-2 space-y-1.5 min-h-0">
      <div v-if="error && !agents.length" class="text-[10px] text-rose-300/90 px-1 py-2">
        {{ error }}
      </div>
      <div v-else-if="loading && !agents.length" class="text-[10px] text-slate-500 italic px-1 py-2">
        Chargement fleet…
      </div>
      <div v-else-if="!agents.length" class="text-[10px] text-slate-500 italic px-1 py-2">
        Aucun agent — Pilot Team hors ligne ?
      </div>

      <button
        v-for="a in agents"
        :key="a.agentId"
        type="button"
        class="w-full text-left rounded-lg border px-2.5 py-2 transition-colors hover:bg-white/5"
        :class="rowClass(a)"
        :title="`Mentionner @${a.agentId}`"
        @click="onMention(a)"
      >
        <div class="flex items-start justify-between gap-2">
          <div class="flex items-center gap-1.5 min-w-0">
            <span
              class="h-1.5 w-1.5 rounded-full shrink-0"
              :class="statusDotClass(a.status)"
              aria-hidden="true"
            />
            <strong class="text-[11px] text-slate-100 truncate">{{ a.displayName }}</strong>
          </div>
          <span class="text-[9px] font-mono text-slate-500 shrink-0">{{ statusLabel(a.status) }}</span>
        </div>
        <div v-if="a.currentAction" class="text-[10px] text-slate-400 truncate mt-0.5 pl-3">
          {{ a.currentAction }}
        </div>
        <div v-else-if="a.role" class="text-[10px] text-slate-500 truncate mt-0.5 pl-3">
          {{ a.role }}
        </div>
        <div
          v-if="a.awaitingHumanApproval"
          class="text-[9px] text-amber-300/90 mt-0.5 pl-3"
        >
          attend L2
        </div>
        <div v-if="a.taskId" class="text-[8px] font-mono text-slate-600 mt-0.5 pl-3 truncate">
          {{ a.taskId.slice(0, 12) }}
        </div>
      </button>

      <section v-if="busMessages.length" class="pt-2 mt-1 border-t border-white/5">
        <h3 class="text-[10px] font-semibold uppercase tracking-widest text-slate-500 px-1 mb-1.5">
          Bus
          <span v-if="inboxCount" class="normal-case tracking-normal text-teal-400/90 font-mono">
            · {{ inboxCount }} pour toi
          </span>
        </h3>
        <ul class="space-y-1">
          <li
            v-for="m in busMessages.slice(0, 6)"
            :key="m.id"
            class="rounded-md border border-white/5 bg-white/[0.02] px-2 py-1.5 text-[9px] text-slate-400 leading-snug"
            :class="m.toAgent === 'compagnon' ? 'border-teal-500/20 bg-teal-500/5' : ''"
          >
            {{ formatBusLine(m) }}
          </li>
        </ul>
      </section>
    </div>

    <div class="shrink-0 border-t border-white/5 px-3 py-2 space-y-1.5">
      <p v-if="jobsHint" class="text-[9px] text-slate-500 leading-snug">{{ jobsHint }}</p>
      <a
        :href="PILOT_LINKS.teamOffice"
        target="_blank"
        rel="noopener noreferrer"
        class="inline-flex items-center gap-1 text-[10px] font-semibold text-teal-300/90 hover:text-teal-200"
      >
        Bureau Team
        <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3 opacity-60" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
        </svg>
      </a>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useAgentsLive } from '../composables/useAgentsLive'
import { useLayout } from '../composables/useLayout'
import { useChat } from '../composables/useChat'
import { statusDotClass, statusLabel } from '../lib/agentsLive.js'
import { formatBusLine } from '../lib/teamBus.js'
import { PILOT_LINKS } from '../lib/pilotLinks.js'

const { toggleAgentsLive } = useLayout()
const { appendMention } = useChat()
const {
  loading,
  error,
  agents,
  jobs,
  l2PendingCount,
  busMessages,
  busyCount,
  inboxCount,
  refresh,
} = useAgentsLive()

const jobsHint = computed(() => {
  const j = jobs.value || {}
  const waiting = Number(j.waiting_approval_count || 0)
  const total = Number(j.total || 0)
  if (!total && !waiting) return ''
  if (waiting) return `Jobs · ${waiting} en attente d’approbation`
  return `Jobs · ${total} suivis`
})

function rowClass(a) {
  if (a.status === 'busy') return 'border-amber-400/25 bg-amber-400/5'
  if (a.status === 'review' || a.awaitingHumanApproval) return 'border-violet-400/25 bg-violet-400/5'
  if (a.status === 'failed') return 'border-rose-400/25 bg-rose-400/5'
  return 'border-white/10 bg-white/[0.02]'
}

function onMention(a) {
  appendMention(`@${a.agentId}`)
}
</script>

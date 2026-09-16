<script setup>
import { ref, computed } from 'vue'
import {
  loadApprovalToken,
  saveApprovalToken,
  hasApprovalToken,
  runRouteFromProposal,
  summarizeRouteResult,
  routeLooksSuccessful,
} from '@/lib/agir'

const props = defineProps({
  proposal: { type: Object, required: true },
  sourceText: { type: String, default: '' },
})

const token = ref(loadApprovalToken())
const busy = ref('')
const lastResult = ref(null)
const lastError = ref('')
const showJson = ref(false)
const tokenInput = ref(null)

const capability = computed(() => props.proposal?.capability || '—')
const summary = computed(() => props.proposal?.summary || 'Action proposée')
const risk = computed(() => props.proposal?.risk_level || '')
const requiresReview = computed(() => Boolean(props.proposal?.requires_review))
const routedTo = computed(() => props.proposal?.routed_to || '')
const actionKind = computed(() => props.proposal?.action?.kind || '')
const tokenReady = computed(() => Boolean(String(token.value || '').trim()) || hasApprovalToken())

function persistToken() {
  saveApprovalToken(token.value.trim())
}

async function run(mode) {
  lastError.value = ''
  if (mode === 'real') {
    const t = String(token.value || '').trim()
    if (!t) {
      lastError.value = 'Jeton requis pour Réel — colle LBG_DESKTOP_APPROVAL_TOKEN (même valeur que Pilot Desktop).'
      try {
        tokenInput.value?.focus()
      } catch {
        /* ignore */
      }
      return
    }
    persistToken()
  }
  busy.value = mode
  try {
    const json = await runRouteFromProposal(props.proposal, mode, {
      text: props.sourceText,
      approvalToken: token.value,
    })
    lastResult.value = {
      mode,
      ok: routeLooksSuccessful(json),
      text: summarizeRouteResult(json, mode),
      raw: json,
    }
  } catch (e) {
    lastError.value = e?.message || String(e)
    lastResult.value = null
  } finally {
    busy.value = ''
  }
}
</script>

<template>
  <div class="mt-4 rounded-2xl border border-cyan-500/30 bg-cyan-500/10 px-3 py-3 space-y-3">
    <div class="flex flex-wrap items-center justify-between gap-2">
      <p class="text-[11px] uppercase tracking-widest font-bold text-cyan-300">Agir · proposition</p>
      <div class="flex flex-wrap gap-1.5 text-[10px] font-mono text-slate-400">
        <span class="px-1.5 py-0.5 rounded border border-cyan-500/30 text-cyan-200/90">{{ capability }}</span>
        <span v-if="actionKind" class="px-1.5 py-0.5 rounded border border-white/10">{{ actionKind }}</span>
        <span v-if="risk" class="px-1.5 py-0.5 rounded border border-amber-500/30 text-amber-200/90">{{ risk }}</span>
      </div>
    </div>

    <p class="text-sm text-slate-100 leading-snug">{{ summary }}</p>
    <p v-if="routedTo" class="text-[11px] text-slate-500 font-mono">→ {{ routedTo }}</p>
    <p v-if="requiresReview" class="text-[11px] text-amber-300/90">
      Revue L2 — Dry-run sans jeton ; Réel exige le jeton desktop.
    </p>

    <label class="block text-[10px] uppercase tracking-wider text-slate-500">
      Token desktop / devops
      <span
        v-if="tokenReady"
        class="ml-1.5 normal-case tracking-normal text-emerald-400/90 font-semibold"
      >· enregistré</span>
      <input
        ref="tokenInput"
        v-model="token"
        type="password"
        autocomplete="off"
        placeholder="coller une fois — mémorisé (et sync Pilot)"
        class="mt-1 w-full max-w-xs rounded-lg border border-white/15 bg-slate-950/80 px-2.5 py-1.5 text-xs text-slate-100 placeholder:text-slate-600 focus:outline-none focus:border-cyan-500/40"
        @change="persistToken"
      />
    </label>

    <div class="flex flex-wrap gap-2 items-center">
      <button
        type="button"
        class="px-2.5 py-1 rounded-lg text-[11px] font-semibold border border-cyan-500/40 text-cyan-200 hover:bg-cyan-500/15 disabled:opacity-40"
        :disabled="!!busy"
        @click="run('dry_run')"
      >
        {{ busy === 'dry_run' ? '…' : 'Dry-run' }}
      </button>
      <button
        type="button"
        class="px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-emerald-500/90 text-slate-950 hover:bg-emerald-400 disabled:opacity-40"
        :disabled="!!busy"
        :title="tokenReady ? 'Exécution réelle' : 'Jeton requis'"
        @click="run('real')"
      >
        {{ busy === 'real' ? '…' : 'Réel' }}
      </button>
      <button
        type="button"
        class="px-2.5 py-1 rounded-lg text-[11px] font-semibold border border-white/15 text-slate-400 hover:text-slate-200"
        @click="showJson = !showJson"
      >
        {{ showJson ? 'Masquer JSON' : 'JSON' }}
      </button>
    </div>

    <pre
      v-if="showJson"
      class="text-[10px] font-mono text-slate-400 bg-slate-950/60 rounded-xl p-2.5 overflow-x-auto max-h-48 border border-white/10"
    >{{ JSON.stringify(proposal, null, 2) }}</pre>

    <p
      v-if="lastError"
      class="text-[11px] font-mono text-red-400"
    >{{ lastError }}</p>
    <p
      v-else-if="lastResult"
      class="text-[11px] font-mono"
      :class="lastResult.ok ? 'text-emerald-400' : 'text-amber-300'"
    >{{ lastResult.text }}</p>
  </div>
</template>

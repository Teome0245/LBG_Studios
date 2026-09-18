<script setup>
import { ref, computed, onMounted } from 'vue'
import {
  loadApprovalToken,
  saveApprovalToken,
  hasApprovalToken,
  bootstrapApprovalToken,
  runRouteFromProposal,
  summarizeRouteResult,
  routeLooksSuccessful,
} from '@/lib/agir'
import { presenceAgirResult } from '@/lib/presence'
import {
  startActivity,
  activityLog,
  activityPhase,
  endActivity,
} from '@/composables/useActivity'

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
const tokenSynced = ref(false)

onMounted(async () => {
  const tok = await bootstrapApprovalToken({ force: true })
  if (tok) {
    token.value = tok
    tokenSynced.value = true
  }
})

const capability = computed(() => props.proposal?.capability || '—')
const summary = computed(() => props.proposal?.summary || 'Action proposée')
const risk = computed(() => props.proposal?.risk_level || '')
const requiresReview = computed(() => Boolean(props.proposal?.requires_review))
const routedTo = computed(() => props.proposal?.routed_to || '')
const actionKind = computed(() => props.proposal?.action?.kind || '')
const tokenReady = computed(() => Boolean(String(token.value || '').trim()) || hasApprovalToken())
const tokenMismatch = computed(() =>
  Boolean(lastResult.value && !lastResult.value.ok && /Jeton incorrect/i.test(lastResult.value.text || ''))
)

function persistToken() {
  saveApprovalToken(token.value.trim())
  if (tokenMismatch.value) {
    lastResult.value = null
    lastError.value = ''
  }
}

async function run(mode) {
  lastError.value = ''
  if (mode === 'real') {
    try {
      const synced = await bootstrapApprovalToken({ force: true })
      if (synced) token.value = synced
    } catch {
      /* ignore */
    }
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
  const label = mode === 'dry_run' ? 'Dry-run' : 'Réel'
  startActivity(`Agir · ${label}`, ['route', props.proposal?.capability || 'desktop'].filter(Boolean))
  activityLog(`${label} · ${props.proposal?.summary || props.proposal?.capability || 'action'}`.slice(0, 160))
  activityPhase('running', mode === 'dry_run' ? 'Simulation…' : 'Exécution…')
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
    activityLog(lastResult.value.text, lastResult.value.ok ? 'ok' : 'warn')
    endActivity(lastResult.value.ok ? 'done' : 'error')
    presenceAgirResult(lastResult.value.ok, lastResult.value.text)
  } catch (e) {
    lastError.value = e?.message || String(e)
    lastResult.value = null
    endActivity('error', lastError.value)
  } finally {
    busy.value = ''
  }
}
</script>

<template>
  <div class="mt-4 rounded-2xl border border-cyan-500/25 bg-slate-900/90 backdrop-blur-xl p-4 space-y-3.5 shadow-xl shadow-black/30">
    <div class="flex flex-wrap items-center justify-between gap-2 border-b border-white/5 pb-2.5">
      <div class="flex items-center gap-2">
        <span class="h-2 w-2 rounded-full bg-cyan-400"></span>
        <p class="text-[11px] uppercase tracking-widest font-bold text-cyan-300">Agir · proposition</p>
      </div>
      <div class="flex flex-wrap gap-1.5 text-[10px] font-mono text-slate-400">
        <span class="px-2 py-0.5 rounded-md border border-cyan-500/30 bg-cyan-500/10 text-cyan-200">{{ capability }}</span>
        <span v-if="actionKind" class="px-2 py-0.5 rounded-md border border-white/10 bg-white/5">{{ actionKind }}</span>
        <span v-if="risk" class="px-2 py-0.5 rounded-md border border-amber-500/30 bg-amber-500/10 text-amber-200">{{ risk }}</span>
      </div>
    </div>

    <p class="text-sm text-slate-100 font-medium leading-relaxed">{{ summary }}</p>
    <p v-if="routedTo" class="text-[11px] text-slate-400 font-mono">Cible : {{ routedTo }}</p>
    <p v-if="requiresReview" class="text-xs text-amber-300/90 bg-amber-500/10 border border-amber-500/20 rounded-xl px-3 py-2">
      Validation L2 requise — Dry-run sans risque ; Réel exige le jeton desktop.
    </p>

    <!-- Token -->
    <div class="pt-1">
      <label class="block text-[10px] uppercase tracking-wider text-slate-400 font-semibold mb-1">
        Jeton desktop / devops
        <span
          v-if="tokenSynced && tokenReady && !tokenMismatch"
          class="ml-1.5 normal-case tracking-normal text-emerald-400 font-medium"
        >· sync .10</span>
        <span
          v-else-if="tokenReady && !tokenMismatch"
          class="ml-1.5 normal-case tracking-normal text-emerald-400 font-medium"
        >· mémorisé</span>
        <span
          v-else-if="tokenMismatch"
          class="ml-1.5 normal-case tracking-normal text-rose-400 font-medium"
        >· ne match pas .10</span>
      </label>
      <input
        ref="tokenInput"
        v-model="token"
        type="password"
        autocomplete="off"
        placeholder="Coller LBG_DESKTOP_APPROVAL_TOKEN (C:\\Agent_IA\\desktop.env)"
        class="w-full max-w-sm rounded-xl border bg-slate-950/80 px-3 py-1.5 text-xs text-slate-100 placeholder:text-slate-600 focus:outline-none"
        :class="tokenMismatch ? 'border-rose-500/50 focus:border-rose-400/60' : 'border-white/10 focus:border-cyan-500/50'"
        @change="persistToken"
        @input="persistToken"
      />
      <p v-if="tokenMismatch" class="mt-1.5 text-[11px] text-rose-300/90 leading-snug max-w-md">
        Le jeton du navigateur ≠ celui de l’agent Windows.
        Ouvre <code class="font-mono text-rose-200/90">C:\Agent_IA\desktop.env</code>,
        copie la valeur de <code class="font-mono text-rose-200/90">LBG_DESKTOP_APPROVAL_TOKEN</code>,
        colle-la ici, puis réessaie <strong>Réel</strong>.
      </p>
    </div>

    <!-- Actions -->
    <div class="flex flex-wrap gap-2 items-center pt-1">
      <button
        type="button"
        class="px-3.5 py-1.5 rounded-xl text-xs font-semibold border border-cyan-500/40 text-cyan-200 bg-cyan-500/10 hover:bg-cyan-500/20 disabled:opacity-40 transition-all cursor-pointer active:scale-95"
        :disabled="!!busy"
        @click="run('dry_run')"
      >
        {{ busy === 'dry_run' ? 'Simulation…' : 'Dry-run (simulation)' }}
      </button>

      <button
        type="button"
        class="px-3.5 py-1.5 rounded-xl text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white disabled:opacity-40 transition-all cursor-pointer shadow-md active:scale-95"
        :disabled="!!busy"
        :title="tokenReady ? 'Exécution réelle' : 'Jeton requis'"
        @click="run('real')"
      >
        {{ busy === 'real' ? 'Exécution…' : 'Réel (exécuter)' }}
      </button>

      <button
        type="button"
        class="px-2.5 py-1.5 rounded-xl text-xs font-medium border border-white/10 text-slate-400 hover:text-slate-200 hover:bg-white/5 transition-colors cursor-pointer"
        @click="showJson = !showJson"
      >
        {{ showJson ? 'Masquer JSON' : 'JSON' }}
      </button>
    </div>

    <pre
      v-if="showJson"
      class="text-[10px] font-mono text-slate-400 bg-slate-950/80 rounded-xl p-3 overflow-x-auto max-h-48 border border-white/10"
    >{{ JSON.stringify(proposal, null, 2) }}</pre>

    <p
      v-if="lastError"
      class="text-xs font-mono text-rose-400 bg-rose-500/10 border border-rose-500/20 rounded-xl p-2.5"
    >{{ lastError }}</p>
    <p
      v-else-if="lastResult"
      class="text-xs font-mono rounded-xl p-2.5 border"
      :class="lastResult.ok ? 'text-emerald-300 bg-emerald-500/10 border-emerald-500/20' : 'text-amber-300 bg-amber-500/10 border-amber-500/20'"
    >{{ lastResult.text }}</p>
  </div>
</template>

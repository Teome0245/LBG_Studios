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
import { presenceAgirResult } from '@/lib/presence'
import {
  startActivity,
  activityLog,
  activityPhase,
  endActivity,
} from '@/composables/useActivity'
import { nextPilotageAfterAgir } from '@/lib/pilotageActions'
import { proposeAction } from '@/lib/agir'
import { useChat } from '@/composables/useChat'
import { PILOT_LINKS } from '@/lib/pilotLinks'

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
const nextBusy = ref('')
const { addUserMessage, addMessage, queuePrompt } = useChat()

const nextSteps = computed(() => {
  if (!lastResult.value) return []
  return nextPilotageAfterAgir({
    capability: props.proposal?.capability,
    ok: lastResult.value.ok,
    mode: lastResult.value.mode,
  })
})

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

async function runNext(step) {
  if (!step || nextBusy.value) return
  if (step.kind === 'link' && step.href) {
    window.open(step.href, '_blank', 'noopener,noreferrer')
    return
  }
  if (step.kind === 'ask' && step.prompt) {
    queuePrompt(step.prompt)
    try {
      window.dispatchEvent(new CustomEvent('compagnon:send-draft'))
    } catch {
      /* ignore */
    }
    return
  }
  if (step.kind !== 'agir' || !step.sourceText) return
  nextBusy.value = step.id
  addUserMessage(`Agir · ${step.label}`)
  try {
    const { proposal, reason } = await proposeAction(step.sourceText)
    if (!proposal) {
      addMessage({
        role: 'assistant',
        content: reason || 'Aucune action sûre.',
        source: 'agir',
      })
    } else {
      addMessage({
        role: 'assistant',
        content: proposal.summary || step.label,
        source: 'agir',
        actionProposal: proposal,
        actionSourceText: step.sourceText,
      })
    }
  } catch (e) {
    addMessage({
      role: 'assistant',
      content: String(e?.message || e),
      source: 'error',
    })
  } finally {
    nextBusy.value = ''
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

    <div v-if="nextSteps.length" class="pt-1 border-t border-white/10 space-y-1.5">
      <p class="text-[10px] uppercase tracking-widest font-bold text-slate-500">Suite — pilotage</p>
      <div class="flex flex-wrap gap-1.5">
        <button
          v-for="s in nextSteps"
          :key="s.id"
          type="button"
          class="text-[11px] px-2.5 py-1 rounded-lg border border-emerald-500/30 bg-emerald-500/10 text-emerald-100 hover:bg-emerald-500/20 disabled:opacity-40"
          :disabled="!!nextBusy || !!busy"
          @click="runNext(s)"
        >
          {{ nextBusy === s.id ? '…' : s.label }}
        </button>
        <a
          class="text-[11px] px-2.5 py-1 rounded-lg border border-white/15 text-slate-400 hover:text-slate-200"
          :href="PILOT_LINKS.jobs"
          target="_blank"
          rel="noopener noreferrer"
        >Pilot Jobs ↗</a>
      </div>
    </div>
  </div>
</template>

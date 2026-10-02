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
  proposeAction,
  reviewProposal,
  isSoftConfirmMode,
  SOFT_CONFIRM_SENTINEL,
} from '@/lib/agir'
import { presenceAgirResult } from '@/lib/presence'
import { nextUsefulAgirSuggestions } from '@/lib/usefulAgirActions'
import { useChat } from '@/composables/useChat'
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
const nextBusy = ref('')
const review = ref(null)
const reviewBusy = ref(false)
const overrideBlock = ref(false)
const softMode = ref(false)
const humanConfirm = ref(false)
const { addUserMessage, addMessage } = useChat()

onMounted(async () => {
  const tok = await bootstrapApprovalToken({ force: true })
  softMode.value = isSoftConfirmMode()
  if (softMode.value) {
    token.value = SOFT_CONFIRM_SENTINEL
    tokenSynced.value = true
  } else if (tok) {
    token.value = tok
    tokenSynced.value = true
  }
  await loadReviewAndMaybeDryRun()
})

async function loadReviewAndMaybeDryRun() {
  reviewBusy.value = true
  try {
    review.value = await reviewProposal(props.proposal, { sourceText: props.sourceText })
    activityLog(
      `Contre-pouvoir · ${review.value.source} · ${review.value.summary || ''}`.slice(0, 160),
      review.value.block_real ? 'warn' : 'ok',
    )
    if (review.value.auto_dry_run && !busy.value && !lastResult.value) {
      await run('dry_run', { fromReview: true })
    }
  } catch (e) {
    review.value = {
      pass: true,
      block_real: false,
      auto_dry_run: false,
      summary: String(e?.message || e),
      risks: [],
      alternatives: [],
      source: 'fallback',
    }
  } finally {
    reviewBusy.value = false
  }
}

const capability = computed(() => props.proposal?.capability || '—')
const summary = computed(() => props.proposal?.summary || 'Action proposée')
const risk = computed(() => props.proposal?.risk_level || '')
const requiresReview = computed(() => Boolean(props.proposal?.requires_review))
const routedTo = computed(() => props.proposal?.routed_to || '')
const actionKind = computed(() => props.proposal?.action?.kind || '')
const tokenReady = computed(() => {
  if (softMode.value) return Boolean(humanConfirm.value)
  return Boolean(String(token.value || '').trim()) || hasApprovalToken()
})
const tokenMismatch = computed(() =>
  Boolean(
    !softMode.value &&
      lastResult.value &&
      !lastResult.value.ok &&
      /Jeton incorrect/i.test(lastResult.value.text || ''),
  ),
)
const realBlocked = computed(
  () => Boolean(review.value?.block_real) && !overrideBlock.value,
)

const nextSuggestions = computed(() => {
  if (!lastResult.value?.ok) return []
  return nextUsefulAgirSuggestions({
    kind: props.proposal?.action?.kind,
    url: props.proposal?.action?.url,
    app: props.proposal?.action?.app,
    capability: props.proposal?.capability,
    sourceText: props.sourceText,
  }, 4)
})

function persistToken() {
  saveApprovalToken(token.value.trim())
  if (tokenMismatch.value) {
    lastResult.value = null
    lastError.value = ''
  }
}

async function proposeNext(intent) {
  if (!intent?.sourceText || nextBusy.value || busy.value) return
  nextBusy.value = intent.id
  const text = intent.sourceText
  addUserMessage(text)
  startActivity(`Agir · ${intent.label}`, ['agir', 'suite'])
  activityLog(`Suite · ${text.slice(0, 100)}`)
  try {
    const { proposal, reason } = await proposeAction(text)
    if (!proposal) {
      activityLog(reason || 'aucune action', 'warn')
      endActivity('error', 'Pas de proposal')
      addMessage({
        role: 'assistant',
        content: reason || 'Aucune action sûre pour cette suite.',
        source: 'agir',
      })
      return
    }
    activityLog(`${proposal.capability || 'ok'} · ${proposal.summary || ''}`.slice(0, 160), 'ok')
    endActivity('done', 'Suite prête')
    addMessage({
      role: 'assistant',
      content: proposal.summary || 'Proposition suivante prête.',
      source: 'agir',
      actionProposal: proposal,
      actionSourceText: text,
    })
  } catch (e) {
    endActivity('error', String(e?.message || e))
    addMessage({
      role: 'assistant',
      content: `Suite impossible : ${e?.message || e}`,
      source: 'error',
    })
  } finally {
    nextBusy.value = ''
  }
}

/**
 * @param {'dry_run'|'real'} mode
 * @param {{ fromReview?: boolean }} [opts]
 */
async function run(mode, opts = {}) {
  lastError.value = ''
  if (mode === 'real') {
    if (realBlocked.value) {
      lastError.value =
        'Contre-pouvoir : Réel verrouillé — coche « Override » après lecture des risques, ou reste en Dry-run.'
      return
    }
    try {
      const synced = await bootstrapApprovalToken({ force: true })
      if (synced) token.value = synced
    } catch {
      /* ignore */
    }
    const t = softMode.value
      ? (humanConfirm.value ? SOFT_CONFIRM_SENTINEL : '')
      : String(token.value || '').trim()
    if (!t) {
      lastError.value = softMode.value
        ? 'Confirmation requise — coche « Je confirme l’exécution réelle ».'
        : 'Jeton requis pour Réel — colle LBG_DESKTOP_APPROVAL_TOKEN (même valeur que Pilot Desktop).'
      try {
        if (!softMode.value) tokenInput.value?.focus()
      } catch {
        /* ignore */
      }
      return
    }
    if (!softMode.value) persistToken()
    else token.value = SOFT_CONFIRM_SENTINEL
  }
  busy.value = mode
  const label = mode === 'dry_run' ? 'Dry-run' : 'Réel'
  if (!opts.fromReview) {
    startActivity(`Agir · ${label}`, ['route', props.proposal?.capability || 'desktop'].filter(Boolean))
    activityLog(`${label} · ${props.proposal?.summary || props.proposal?.capability || 'action'}`.slice(0, 160))
    activityPhase('running', mode === 'dry_run' ? 'Simulation…' : 'Exécution…')
  } else {
    activityLog('Auto dry-run (contre-pouvoir)…')
  }
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
    if (!opts.fromReview) {
      endActivity(lastResult.value.ok ? 'done' : 'error')
    }
    presenceAgirResult(lastResult.value.ok, lastResult.value.text)
  } catch (e) {
    lastError.value = e?.message || String(e)
    lastResult.value = null
    if (!opts.fromReview) endActivity('error', lastError.value)
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
        <span
          v-if="reviewBusy"
          class="px-2 py-0.5 rounded-md border border-violet-500/30 bg-violet-500/10 text-violet-200"
        >revue…</span>
        <span
          v-else-if="review"
          class="px-2 py-0.5 rounded-md border"
          :class="review.block_real
            ? 'border-rose-500/40 bg-rose-500/10 text-rose-200'
            : 'border-violet-500/30 bg-violet-500/10 text-violet-200'"
        >contre-pouvoir · {{ review.source }}</span>
      </div>
    </div>

    <p class="text-sm text-slate-100 font-medium leading-relaxed">{{ summary }}</p>
    <p v-if="routedTo" class="text-[11px] text-slate-400 font-mono">Cible : {{ routedTo }}</p>
    <p v-if="requiresReview" class="text-xs text-amber-300/90 bg-amber-500/10 border border-amber-500/20 rounded-xl px-3 py-2">
      Validation L2 requise — Dry-run sans risque ; Réel exige le jeton desktop.
    </p>

    <div
      v-if="review && (review.summary || review.risks?.length)"
      class="text-xs rounded-xl px-3 py-2 border space-y-1.5"
      :class="review.block_real
        ? 'text-rose-100/95 bg-rose-500/10 border-rose-500/25'
        : 'text-violet-100/95 bg-violet-500/10 border-violet-500/25'"
    >
      <p class="font-semibold tracking-wide uppercase text-[10px] opacity-80">Contre-pouvoir (pas Lyra)</p>
      <p class="leading-relaxed">{{ review.summary }}</p>
      <ul v-if="review.risks?.length" class="list-disc pl-4 space-y-0.5 text-[11px] opacity-90">
        <li v-for="(rk, i) in review.risks" :key="i">{{ rk }}</li>
      </ul>
      <ul v-if="review.alternatives?.length" class="list-disc pl-4 space-y-0.5 text-[11px] text-teal-200/90">
        <li v-for="(a, i) in review.alternatives" :key="'a'+i">{{ a }}</li>
      </ul>
      <label
        v-if="review.block_real"
        class="flex items-center gap-2 pt-1 text-[11px] text-rose-100 cursor-pointer select-none"
      >
        <input v-model="overrideBlock" type="checkbox" class="rounded border-rose-400/50" />
        Override humain — je confirme le Réel malgré l’avis
      </label>
    </div>

    <div class="pt-1">
      <template v-if="softMode">
        <label class="flex items-start gap-2.5 text-xs text-slate-200 cursor-pointer select-none rounded-xl border border-emerald-500/25 bg-emerald-500/10 px-3 py-2.5">
          <input v-model="humanConfirm" type="checkbox" class="mt-0.5 rounded border-emerald-400/50" />
          <span>
            <span class="font-semibold text-emerald-200">Je confirme l’exécution réelle</span>
            <span class="block text-[11px] text-emerald-100/70 mt-0.5 leading-snug">
              LAB LAN — pas de jeton secret. Le contre-pouvoir + cette case remplacent l’approbation.
            </span>
          </span>
        </label>
      </template>
      <template v-else>
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
      </template>
    </div>

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
        :disabled="!!busy || realBlocked || (softMode && !humanConfirm)"
        :title="realBlocked ? 'Contre-pouvoir : override requis' : (tokenReady ? 'Exécution réelle' : (softMode ? 'Confirmation requise' : 'Jeton requis'))"
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
    >{{ JSON.stringify({ proposal, review }, null, 2) }}</pre>

    <p
      v-if="lastError"
      class="text-xs font-mono text-rose-400 bg-rose-500/10 border border-rose-500/20 rounded-xl p-2.5"
    >{{ lastError }}</p>
    <p
      v-else-if="lastResult"
      class="text-xs font-mono rounded-xl p-2.5 border"
      :class="lastResult.ok ? 'text-emerald-300 bg-emerald-500/10 border-emerald-500/20' : 'text-amber-300 bg-amber-500/10 border-amber-500/20'"
    >{{ lastResult.text }}</p>

    <div
      v-if="nextSuggestions.length"
      class="pt-1 border-t border-white/5 space-y-2"
    >
      <p class="text-[10px] uppercase tracking-wider text-slate-500 font-semibold">Ensuite — actions utiles</p>
      <div class="flex flex-wrap gap-1.5">
        <button
          v-for="s in nextSuggestions"
          :key="s.id"
          type="button"
          class="px-2.5 py-1.5 rounded-lg text-[11px] font-medium border border-teal-500/25 bg-teal-500/10 text-teal-100 hover:bg-teal-500/20 disabled:opacity-40 transition-colors cursor-pointer text-left"
          :disabled="!!busy || !!nextBusy"
          :title="s.sourceText"
          @click="proposeNext(s)"
        >
          <span class="font-semibold">{{ nextBusy === s.id ? '…' : s.label }}</span>
          <span v-if="s.hint" class="block text-[10px] text-teal-200/60 font-normal">{{ s.hint }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

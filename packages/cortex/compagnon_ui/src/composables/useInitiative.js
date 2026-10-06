import { ref, onMounted, computed } from 'vue'
import {
  INITIATIVE_DEFAULTS,
  shouldOfferFromStatus,
  markInitiativeShown,
  snoozeInitiative,
  formatDiscussReply,
  recordInitiativeFeedback,
  canShowInitiative,
} from '@/lib/initiativeQuota'
import { getStudioGoal, biasGoalFromThemes } from '@/lib/studioGoal'
import { presenceInitiative } from '@/lib/presence'
import { speakText } from '@/lib/tts'
import { fetchSelfStatus, formatSelfLine, offerFromSelf, offerFromEvolutionSeed } from '@/lib/selfPresence'
import {
  spiceInitiative,
  sendSpontaneityFeedback,
  toToastPayload,
  fetchEvolution,
  topEvolutionSeed,
} from '@/lib/spontaneity'
import {
  willAutoValidateEnabled,
  consumePendingWill,
} from '@/lib/willPolicy'
import { proposeAction, runRouteFromProposal, summarizeRouteResult } from '@/lib/agir'
import { spawnTeamL1, teamObjectiveFromInitiative } from '@/lib/teamSpawn'
import { useChat } from '@/composables/useChat'

const current = ref(null)
const lastError = ref('')
const lastStatus = ref(null)
const lastSelf = ref(null)
const proposing = ref(false)
const studioGoal = ref(getStudioGoal())
let timer = null
let started = false
let spiceBusy = false
let autoBusy = false
/** @type {Set<string>} */
const autoTried = new Set()

const selfLine = computed(() => formatSelfLine(lastSelf.value))

async function fetchStatus() {
  const res = await fetch('/api/pilot/orchestrator/proactive/status', {
    headers: { Accept: 'application/json' },
  })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

/**
 * @param {import('@/lib/spontaneity').InitiativeOffer} offer
 * @param {{ fromSelf?: boolean }} [opts]
 */
async function applyOffer(offer, opts = {}) {
  if (!offer?.offer) return false
  const gate = canShowInitiative(offer.id)
  if (!gate.ok) return false
  if (spiceBusy) return false
  spiceBusy = true
  try {
    const spiced = await spiceInitiative(
      { ...offer, fromSelf: Boolean(opts.fromSelf || offer.fromSelf) },
      {
        selfLine: selfLine.value,
        goalTitle: offer.goal?.title || studioGoal.value?.goal?.title || '',
      },
    )
    if (current.value) return false
    const gate2 = canShowInitiative(spiced.id)
    if (!gate2.ok) return false
    current.value = toToastPayload(
      {
        ...spiced,
        willId: offer.willId || spiced.willId,
        willKind: offer.willKind || spiced.willKind,
        autoValidate: offer.autoValidate ?? spiced.autoValidate,
      },
      { fromSelf: Boolean(opts.fromSelf || offer.fromSelf) },
    )
    markInitiativeShown(spiced.id)
    presenceInitiative(spiced.message)
    void speakText(String(spiced.message || '').slice(0, 220)).catch(() => {
      /* best-effort */
    })
    return true
  } finally {
    spiceBusy = false
  }
}

/**
 * Auto L1 lecture seule — morning_brief ou smoke Team.
 * @param {{ willId?: string, autoValidate?: string|null, intents?: object[], message?: string, id?: string }} offer
 */
async function tryAutoValidateWill(offer) {
  if (!willAutoValidateEnabled()) return false
  if (!offer?.autoValidate || !offer.willId) return false
  if (autoBusy || autoTried.has(offer.willId)) return false
  autoBusy = true
  autoTried.add(offer.willId)
  const { addUserMessage, addMessage } = useChat()
  try {
    if (offer.autoValidate === 'brief') {
      addUserMessage('Auto · Brief du matin')
      const { proposal, reason } = await proposeAction('fais mon brief du matin')
      if (!proposal) {
        addMessage({
          role: 'assistant',
          content: reason || 'Brief auto : aucune action reconnue.',
          source: 'will-auto',
        })
        return false
      }
      const route = await runRouteFromProposal(proposal, 'real', {
        text: 'fais mon brief du matin',
      })
      addMessage({
        role: 'assistant',
        content: `Envie auto-validée (brief, lecture seule).\n${summarizeRouteResult(route, 'real')}`,
        source: 'will-auto',
        state: 'orchestrateur-happy',
      })
      await consumePendingWill(offer.willId, 'complete', 'auto_brief')
      snoozeInitiative(offer.id || `self:will:${offer.willId}`, 6)
      return true
    }
    if (offer.autoValidate === 'team_l1') {
      const intent = offer.intents?.find((i) => i.teamSpawn) || offer.intents?.[0]
      const objective = teamObjectiveFromInitiative(offer.message, intent?.teamObjective)
      addUserMessage('Auto · Team L1 (envie smoke)')
      const out = await spawnTeamL1({
        objective,
        role: intent?.teamRole || 'qa',
        context: { initiative_id: offer.id || '', will_id: offer.willId },
        run: true,
      })
      if (!out.ok) {
        addMessage({
          role: 'assistant',
          content: `Auto Team L1 impossible : ${out.error || 'erreur'}`,
          source: 'will-auto',
        })
        return false
      }
      addMessage({
        role: 'assistant',
        content:
          `Envie smoke auto-déléguée Team L1 (${out.role}) : tâche ${out.id || '?'}.` +
          `\nPas de Réel desktop — suivi Pilot #/team.`,
        source: 'will-auto',
        state: 'orchestrateur-happy',
      })
      await consumePendingWill(offer.willId, 'complete', 'auto_team_l1')
      snoozeInitiative(offer.id || `self:will:${offer.willId}`, 6)
      return true
    }
    return false
  } catch (e) {
    addMessage({
      role: 'assistant',
      content: `Auto-validate envie échoué : ${e?.message || e}`,
      source: 'error',
    })
    return false
  } finally {
    autoBusy = false
  }
}

async function tick() {
  try {
    studioGoal.value = getStudioGoal()
    const [status, selfStatus, evo] = await Promise.all([
      fetchStatus(),
      fetchSelfStatus(),
      fetchEvolution(),
    ])
    lastStatus.value = status
    lastSelf.value = selfStatus
    lastError.value = ''
    if (current.value || spiceBusy || autoBusy) return

    const offer = shouldOfferFromStatus(status)
    if (await applyOffer(offer)) return

    const selfOffer = offerFromSelf(selfStatus)
    if (selfOffer.offer) {
      if (await tryAutoValidateWill(selfOffer)) {
        lastSelf.value = await fetchSelfStatus()
        return
      }
      if (await applyOffer({ ...selfOffer, primary: selfOffer.intents?.[0] || null }, { fromSelf: true })) {
        return
      }
    }

    // Fallback évolution : seed scorée si rien d'autre
    const evoOffer = offerFromEvolutionSeed(topEvolutionSeed(evo))
    if (evoOffer.offer) {
      if (await tryAutoValidateWill(evoOffer)) {
        lastSelf.value = await fetchSelfStatus()
        return
      }
      await applyOffer({ ...evoOffer, primary: evoOffer.intents?.[0] || null }, { fromSelf: true })
    }
  } catch (e) {
    lastError.value = e?.message || String(e)
  }
}

/**
 * Ferme le toast et snooze explicitement le signal.
 * @param {number} [snoozeHours=4]
 * @param {'dismiss'|'accept'|'discuss'} [feedback='dismiss']
 */
function dismiss(snoozeHours = 4, feedback = 'dismiss') {
  if (current.value?.id) {
    const kind = feedback === 'accept' ? 'accept' : 'dismiss'
    recordInitiativeFeedback(current.value.id, kind)
    sendSpontaneityFeedback({
      id: current.value.id,
      kind,
      themes: current.value.themes || [],
      message: current.value.message || '',
      evolution_seed: current.value.evolution_seed || null,
    })
    if (kind === 'accept' && current.value.themes?.length) {
      biasGoalFromThemes(current.value.themes)
      studioGoal.value = getStudioGoal()
    }
    const willId = current.value.willId
    // discuss = snooze toast seulement ; AGIR/Team = complete ; Ignorer = dismiss
    if (willId && feedback !== 'discuss') {
      void consumePendingWill(willId, kind === 'accept' ? 'complete' : 'dismiss', kind)
    }
    snoozeInitiative(current.value.id, snoozeHours)
  }
  current.value = null
}

function discussText() {
  const init = current.value
  const goal = init?.goal || studioGoal.value?.goal || null
  const base = formatDiscussReply(lastStatus.value || {}, {
    message: init?.message || '',
    intents: init?.intents || [],
    goal,
    offerType: init?.offerType,
    kind: init?.kind,
  })
  const selfBit = selfLine.value ? `\n\nSelf : ${selfLine.value}` : ''
  const spont =
    init?.spontaneous
      ? `\n\nSpontané (${init.spice_mode || 'full'}) — themes : ${(init.themes || []).join(', ') || '—'}`
      : ''
  // Objectif déjà dans le corps si goal toast/studio ; éviter un 2e bloc décalé
  return `${base}${selfBit}${spont}`
}

export function useInitiative() {
  onMounted(() => {
    if (started) return
    started = true
    tick()
    timer = setInterval(tick, INITIATIVE_DEFAULTS.pollIntervalMs)
  })

  return {
    current,
    lastError,
    lastStatus,
    lastSelf,
    selfLine,
    proposing,
    studioGoal,
    dismiss,
    discussText,
    refresh: tick,
  }
}

export function stopInitiativePolling() {
  if (timer) clearInterval(timer)
  timer = null
  started = false
  spiceBusy = false
  autoBusy = false
}

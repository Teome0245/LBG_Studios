import { ref, onMounted } from 'vue'
import {
  INITIATIVE_DEFAULTS,
  shouldOfferFromStatus,
  markInitiativeShown,
  snoozeInitiative,
  formatDiscussReply,
  recordInitiativeFeedback,
} from '@/lib/initiativeQuota'
import { getStudioGoal } from '@/lib/studioGoal'
import { presenceInitiative } from '@/lib/presence'

const current = ref(null)
const lastError = ref('')
const lastStatus = ref(null)
const proposing = ref(false)
const studioGoal = ref(getStudioGoal())
let timer = null
let started = false

async function fetchStatus() {
  const res = await fetch('/api/pilot/orchestrator/proactive/status', {
    headers: { Accept: 'application/json' },
  })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

async function tick() {
  try {
    studioGoal.value = getStudioGoal()
    const status = await fetchStatus()
    lastStatus.value = status
    lastError.value = ''
    if (current.value) return
    const offer = shouldOfferFromStatus(status)
    if (!offer.offer) return
    current.value = {
      id: offer.id,
      message: offer.message,
      kind: offer.kind,
      intents: offer.intents || [],
      primary: offer.primary || null,
      goal: offer.goal || null,
      at: Date.now(),
    }
    markInitiativeShown(offer.id)
    presenceInitiative(offer.message)
  } catch (e) {
    lastError.value = e?.message || String(e)
  }
}

/**
 * Ferme le toast et snooze explicitement le signal.
 * @param {number} [snoozeHours=4]
 * @param {'dismiss'|'accept'} [feedback='dismiss']
 */
function dismiss(snoozeHours = 4, feedback = 'dismiss') {
  if (current.value?.id) {
    recordInitiativeFeedback(current.value.id, feedback === 'accept' ? 'accept' : 'dismiss')
    snoozeInitiative(current.value.id, snoozeHours)
  }
  current.value = null
}

function discussText() {
  const base = formatDiscussReply(lastStatus.value || {})
  const g = studioGoal.value?.goal
  if (!g) return base
  return `${base}\n\nObjectif actif : ${g.title} — ${g.description}`
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
}

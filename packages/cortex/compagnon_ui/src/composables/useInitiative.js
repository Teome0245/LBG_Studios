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
import { getStudioGoal } from '@/lib/studioGoal'
import { presenceInitiative } from '@/lib/presence'
import { fetchSelfStatus, formatSelfLine, offerFromSelf } from '@/lib/selfPresence'

const current = ref(null)
const lastError = ref('')
const lastStatus = ref(null)
const lastSelf = ref(null)
const proposing = ref(false)
const studioGoal = ref(getStudioGoal())
let timer = null
let started = false

const selfLine = computed(() => formatSelfLine(lastSelf.value))

async function fetchStatus() {
  const res = await fetch('/api/pilot/orchestrator/proactive/status', {
    headers: { Accept: 'application/json' },
  })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

function applyOffer(offer) {
  if (!offer?.offer) return false
  const gate = canShowInitiative(offer.id)
  if (!gate.ok) return false
  current.value = {
    id: offer.id,
    message: offer.message,
    kind: offer.kind,
    intents: offer.intents || [],
    primary: offer.primary || offer.intents?.[0] || null,
    goal: offer.goal || null,
    at: Date.now(),
    fromSelf: Boolean(offer.fromSelf),
  }
  markInitiativeShown(offer.id)
  presenceInitiative(offer.message)
  return true
}

async function tick() {
  try {
    studioGoal.value = getStudioGoal()
    const [status, selfStatus] = await Promise.all([fetchStatus(), fetchSelfStatus()])
    lastStatus.value = status
    lastSelf.value = selfStatus
    lastError.value = ''
    if (current.value) return

    const offer = shouldOfferFromStatus(status)
    if (applyOffer(offer)) return

    const selfOffer = offerFromSelf(selfStatus)
    if (selfOffer.offer) {
      applyOffer({ ...selfOffer, fromSelf: true, primary: selfOffer.intents?.[0] || null })
    }
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
  const selfBit = selfLine.value ? `\n\nSelf : ${selfLine.value}` : ''
  if (!g) return `${base}${selfBit}`
  return `${base}\n\nObjectif actif : ${g.title} — ${g.description}${selfBit}`
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
}

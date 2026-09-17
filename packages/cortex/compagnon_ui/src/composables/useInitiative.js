import { ref, onMounted } from 'vue'
import {
  INITIATIVE_DEFAULTS,
  shouldOfferFromStatus,
  markInitiativeShown,
  formatDiscussReply,
} from '@/lib/initiativeQuota'
import { presenceInitiative } from '@/lib/presence'

const current = ref(null)
const lastError = ref('')
const lastStatus = ref(null)
const proposing = ref(false)
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
      at: Date.now(),
    }
    markInitiativeShown(offer.id)
    presenceInitiative(offer.message)
  } catch (e) {
    lastError.value = e?.message || String(e)
  }
}

function dismiss() {
  current.value = null
}

function discussText() {
  return formatDiscussReply(lastStatus.value || {})
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

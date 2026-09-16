import { ref, onMounted, onUnmounted } from 'vue'
import {
  INITIATIVE_DEFAULTS,
  shouldOfferFromStatus,
  markInitiativeShown,
  formatDiscussReply,
} from '@/lib/initiativeQuota'

const current = ref(null)
const lastError = ref('')
/** Dernier status brut (pour Discuter → propositions concrètes). */
const lastStatus = ref(null)
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
      at: Date.now(),
    }
    markInitiativeShown(offer.id)
  } catch (e) {
    lastError.value = e?.message || String(e)
  }
}

function dismiss() {
  current.value = null
}

/** Texte de discussion locale (pas de POST /ask). */
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

  onUnmounted(() => {
    // singleton — ne pas clear si d'autres consumers (App only)
  })

  return {
    current,
    lastError,
    lastStatus,
    dismiss,
    discussText,
    refresh: tick,
  }
}

/** Arrêt explicite (tests / HMR). */
export function stopInitiativePolling() {
  if (timer) clearInterval(timer)
  timer = null
  started = false
}

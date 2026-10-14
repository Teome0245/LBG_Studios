/**
 * Poll fleet Team quand le side-panel Agents live est ouvert.
 */
import { computed, onUnmounted, ref, watch } from 'vue'
import { fetchAgentsLive } from '../lib/agentsLive.js'
import { COMPAGNON_BUS_AGENT, listMessages } from '../lib/teamBus.js'
import { useLayout } from './useLayout'

const POLL_MS = 8000

const loading = ref(false)
const error = ref('')
const agents = ref([])
const metrics = ref({})
const jobs = ref({})
const campus = ref({})
const l2PendingCount = ref(0)
const busMessages = ref([])
const lastFetchAt = ref(0)

let intervalId = null
let abortCtrl = null
let watchersStarted = false

async function refresh() {
  if (abortCtrl) abortCtrl.abort()
  abortCtrl = new AbortController()
  loading.value = true
  try {
    const [snap, bus] = await Promise.all([
      fetchAgentsLive({ signal: abortCtrl.signal }),
      listMessages({ limit: 12, signal: abortCtrl.signal }).catch(() => ({
        ok: false,
        messages: [],
      })),
    ])
    if (snap.error && !snap.agents?.length) {
      error.value = snap.error
    } else {
      error.value = ''
    }
    agents.value = snap.agents || []
    metrics.value = snap.metrics || {}
    jobs.value = snap.jobs || {}
    campus.value = snap.campus || {}
    l2PendingCount.value = snap.l2PendingCount || 0
    busMessages.value = (bus.messages || []).slice(0, 12)
    lastFetchAt.value = Date.now()
  } catch (e) {
    if (e?.name === 'AbortError') return
    error.value = e?.message || 'fleet indisponible'
  } finally {
    loading.value = false
  }
}

function stopPoll() {
  if (intervalId) {
    clearInterval(intervalId)
    intervalId = null
  }
  if (abortCtrl) {
    abortCtrl.abort()
    abortCtrl = null
  }
}

function startPoll() {
  stopPoll()
  void refresh()
  intervalId = setInterval(() => {
    void refresh()
  }, POLL_MS)
}

function ensureWatchers() {
  if (watchersStarted) return
  watchersStarted = true
  const { agentsLiveCollapsed } = useLayout()
  watch(
    agentsLiveCollapsed,
    (collapsed) => {
      if (collapsed) stopPoll()
      else startPoll()
    },
    { immediate: true },
  )
}

export function useAgentsLive() {
  ensureWatchers()

  const busyCount = computed(
    () => agents.value.filter((a) => a.status === 'busy' || a.status === 'review').length,
  )
  const hasLive = computed(() => agents.value.length > 0)
  const inboxCount = computed(
    () =>
      busMessages.value.filter(
        (m) => m.toAgent === COMPAGNON_BUS_AGENT && (m.kind === 'verify_result' || m.kind === 'ack'),
      ).length,
  )

  onUnmounted(() => {
    /* singleton poll — ne pas stop ici (plusieurs composants) */
  })

  return {
    loading,
    error,
    agents,
    metrics,
    jobs,
    campus,
    l2PendingCount,
    busMessages,
    lastFetchAt,
    busyCount,
    hasLive,
    inboxCount,
    refresh,
  }
}

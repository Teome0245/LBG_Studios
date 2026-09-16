import { computed, ref, watch } from 'vue'

const HIST_KEY = 'lbg_orch_hist_collapsed'
/** v3 : défaut fermé (canal chat type OWUI) — remplace v2 coincé ouvert */
const INFRA_KEY = 'lbg_orch_infra_collapsed_v3'
const MONITOR_KEY = 'lbg_orch_monitor_collapsed_v3'
const LYRA_KEY = 'lbg_orch_lyra_minimized'
/** v2 : bannière Pilot masquée par défaut (chat-first) */
const BANNER_KEY = 'lbg_orch_pilot_banner_dismissed_v2'
const OPS_METRICS_KEY = 'lbg_orch_ops_metrics_v1'

function loadBool(key, fallback = false) {
  try {
    const v = localStorage.getItem(key)
    if (v === null) return fallback
    return v === '1' || v === 'true'
  } catch {
    return fallback
  }
}

function saveBool(key, value) {
  try {
    localStorage.setItem(key, value ? '1' : '0')
  } catch {
    /* ignore */
  }
}

const histCollapsed = ref(
  loadBool(HIST_KEY, loadBool('lbg_orch_sidebar_collapsed', false))
)
/** Étape B : infra + monitor fermés par défaut */
const infraCollapsed = ref(loadBool(INFRA_KEY, true))
const monitorCollapsed = ref(loadBool(MONITOR_KEY, true))
const lyraMinimized = ref(loadBool(LYRA_KEY, true))
/** Continuité : pas de bandeau ops au premier écran */
const pilotBannerDismissed = ref(loadBool(BANNER_KEY, true))
/** CPU/RAM header — off par défaut */
const opsMetricsVisible = ref(loadBool(OPS_METRICS_KEY, false))

watch(histCollapsed, (v) => saveBool(HIST_KEY, v))
watch(infraCollapsed, (v) => saveBool(INFRA_KEY, v))
watch(monitorCollapsed, (v) => saveBool(MONITOR_KEY, v))
watch(lyraMinimized, (v) => saveBool(LYRA_KEY, v))
watch(pilotBannerDismissed, (v) => saveBool(BANNER_KEY, v))
watch(opsMetricsVisible, (v) => saveBool(OPS_METRICS_KEY, v))

export function useLayout() {
  const toggleHist = () => {
    histCollapsed.value = !histCollapsed.value
  }
  const toggleInfra = () => {
    infraCollapsed.value = !infraCollapsed.value
  }
  const toggleMonitor = () => {
    monitorCollapsed.value = !monitorCollapsed.value
  }
  const toggleLyra = () => {
    lyraMinimized.value = !lyraMinimized.value
  }
  const dismissPilotBanner = () => {
    pilotBannerDismissed.value = true
  }
  const toggleOpsMetrics = () => {
    opsMetricsVisible.value = !opsMetricsVisible.value
  }

  /** Alias rétrocompat */
  const leftCollapsed = histCollapsed
  const rightCollapsed = monitorCollapsed
  const toggleLeft = toggleHist
  const toggleRight = toggleMonitor

  /** Rail nav = 3.5rem (w-14) + hist 16rem (w-64) ; droite = infra 16rem + monitor 18rem */
  const chatInputOffsetClass = computed(() => {
    const left = histCollapsed.value ? 'sm:left-14' : 'sm:left-[19.5rem]'
    let right = 'right-0'
    const infraOpen = !infraCollapsed.value
    const monOpen = !monitorCollapsed.value
    if (infraOpen && monOpen) right = 'lg:right-[34rem]'
    else if (infraOpen) right = 'lg:right-64'
    else if (monOpen) right = 'lg:right-72'
    return `left-0 ${left} ${right}`
  })

  return {
    histCollapsed,
    infraCollapsed,
    monitorCollapsed,
    lyraMinimized,
    pilotBannerDismissed,
    opsMetricsVisible,
    toggleHist,
    toggleInfra,
    toggleMonitor,
    toggleLyra,
    dismissPilotBanner,
    toggleOpsMetrics,
    leftCollapsed,
    rightCollapsed,
    toggleLeft,
    toggleRight,
    chatInputOffsetClass,
  }
}

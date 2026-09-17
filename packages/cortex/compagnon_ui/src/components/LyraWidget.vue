<template>
  <!-- Desktop Pet — présence bas-droite (vie + bulle Agir) -->
  <div class="pet-root pointer-events-none">
    <Transition name="pet-pop">
      <div
        v-if="resultBanner"
        class="pet-result pointer-events-auto"
        :class="resultBanner.ok === false ? 'is-warn' : 'is-ok'"
        role="status"
      >
        <p class="pet-result-label">{{ resultBanner.label }}</p>
        <p class="pet-result-msg">{{ resultBanner.text }}</p>
        <button type="button" class="pet-btn-later" @click="resultBanner = null">OK</button>
      </div>
    </Transition>

    <Transition name="pet-pop">
      <div
        v-if="bubbleOpen && current"
        class="pet-bubble pointer-events-auto"
        role="status"
        aria-live="polite"
      >
        <p class="pet-bubble-msg">{{ current.message }}</p>
        <div v-if="current.primary" class="pet-bubble-actions">
          <button
            type="button"
            class="pet-btn-agir"
            :disabled="proposing"
            @click="runPrimary"
          >
            {{ proposing ? '…' : current.primary.label }}
          </button>
          <button type="button" class="pet-btn-later" @click="dismissBubble">Plus tard</button>
        </div>
        <p v-if="current.primary?.hint" class="pet-hint">{{ current.primary.hint }}</p>
      </div>
    </Transition>

    <Transition name="pet-pop">
      <div v-if="statusChip && !resultBanner" class="pet-chip pointer-events-none">{{ statusChip }}</div>
    </Transition>

    <button
      type="button"
      class="pet-avatar pointer-events-auto"
      :class="{ alert: !!current && bubbleOpen, live: !!statusChip }"
      :title="lyraMinimized ? 'Ouvrir Compagnon' : 'Présence Compagnon'"
      @click="onAvatarClick"
    >
      <div id="pet-face-host" ref="faceHost" class="pet-face" aria-hidden="true" />
      <span class="pet-dot" :class="moodDot" />
    </button>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useLayout } from '../composables/useLayout'
import { useInitiative } from '../composables/useInitiative'
import { useChat } from '../composables/useChat'
import { proposeAction } from '@/lib/agir'
import { onPresence } from '@/lib/presence'

const { lyraMinimized, toggleLyra } = useLayout()
const { current, dismiss, proposing } = useInitiative()
const { addUserMessage, addMessage } = useChat()

const faceHost = ref(null)
const bubbleOpen = ref(false)
const statusChip = ref('')
const resultBanner = ref(null)
const gauges = ref({ energie: 50, chaleur: 50 })
let faceInst = null
let pollId = null
let chipTimer = null
let resultTimer = null
let unsubPresence = null

const moodDot = computed(() => {
  const e = Number(gauges.value?.energie) || 50
  if (current.value) return 'dot-alert'
  if (e > 70) return 'dot-ok'
  if (e > 40) return 'dot-warn'
  return 'dot-low'
})

watch(current, (v) => {
  bubbleOpen.value = !!v
  if (faceInst?.ready) {
    faceInst.setMood(v ? 'tense' : 'serene')
    if (v) faceInst.pulse?.('alert')
  }
})

function dismissBubble() {
  bubbleOpen.value = false
  dismiss()
  if (faceInst?.ready) faceInst.setMood('serene')
}

async function runPrimary() {
  const intent = current.value?.primary
  if (!intent?.sourceText || proposing.value) return
  proposing.value = true
  addUserMessage(`Agir · ${intent.label || intent.sourceText}`)
  try {
    const { proposal, reason } = await proposeAction(intent.sourceText)
    if (!proposal) {
      addMessage({
        role: 'assistant',
        content: reason || 'Aucune action sûre reconnue.',
        source: 'agir',
      })
    } else {
      addMessage({
        role: 'assistant',
        content: proposal.summary || intent.label || 'Proposition prête — Dry-run puis Réel.',
        source: 'agir',
        actionProposal: proposal,
        actionSourceText: intent.sourceText,
      })
    }
    dismissBubble()
  } catch (e) {
    addMessage({
      role: 'assistant',
      content: `Proposition impossible : ${e?.message || e}`,
      source: 'error',
    })
  } finally {
    proposing.value = false
  }
}

function onAvatarClick() {
  if (current.value && !bubbleOpen.value) {
    bubbleOpen.value = true
    return
  }
  if (current.value && bubbleOpen.value) {
    runPrimary()
    return
  }
  // Tickle : petit clin d’œil
  if (faceInst?.ready) {
    faceInst.setExpression?.('surprised')
    faceInst.say?.('hey')
    faceInst.pulse?.('ok')
    showChip('hey')
    setTimeout(() => faceInst?.setMood?.('serene'), 1200)
  }
  toggleLyra()
}

function showChip(text) {
  statusChip.value = text
  if (chipTimer) clearTimeout(chipTimer)
  chipTimer = setTimeout(() => {
    statusChip.value = ''
  }, 2200)
}

function showResult(evt) {
  if (!evt?.result && !evt?.label) return
  resultBanner.value = {
    label: evt.label || 'Résultat',
    text: evt.result || evt.label,
    ok: evt.pulse !== 'warn' && evt.pulse !== 'alert',
  }
  if (resultTimer) clearTimeout(resultTimer)
  resultTimer = setTimeout(() => {
    resultBanner.value = null
  }, evt.holdMs || 8000)
}

function ensureFaceAssets() {
  return new Promise((resolve) => {
    if (window.FaceRig) {
      resolve()
      return
    }
    if (!document.getElementById('face-rig-css')) {
      const link = document.createElement('link')
      link.id = 'face-rig-css'
      link.rel = 'stylesheet'
      link.href = '/face_rig/face_rig.css'
      document.head.appendChild(link)
    }
    const existing = document.getElementById('face-rig-js')
    if (existing) {
      existing.addEventListener('load', () => resolve(), { once: true })
      if (window.FaceRig) resolve()
      return
    }
    const script = document.createElement('script')
    script.id = 'face-rig-js'
    script.src = '/face_rig/face_rig.js'
    script.onload = () => resolve()
    script.onerror = () => resolve()
    document.body.appendChild(script)
  })
}

async function initFace() {
  await ensureFaceAssets()
  await nextTick()
  const host = document.getElementById('pet-face-host')
  if (!host || !window.FaceRig) return
  try {
    faceInst =
      typeof window.FaceRig.create === 'function'
        ? window.FaceRig.create()
        : window.FaceRig
    await faceInst.init(host, { characterId: 'lyra_assistant' })
    faceInst.setMood('serene')
  } catch (e) {
    console.warn('pet FaceRig', e)
  }
}

async function fetchGauges() {
  try {
    const res = await fetch('/lyra/state', { headers: { Accept: 'application/json' } })
    if (!res.ok) return
    const data = await res.json()
    if (data?.gauges) gauges.value = data.gauges
  } catch {
    /* offline */
  }
}

onMounted(() => {
  initFace()
  fetchGauges()
  pollId = setInterval(fetchGauges, 12_000)
  unsubPresence = onPresence((evt) => {
    if (evt?.result) {
      showResult(evt)
      return
    }
    if (evt?.label) showChip(evt.label)
    else if (evt?.pulse === 'ok') showChip('ok')
    else if (evt?.pulse === 'alert') showChip('!')
  })
})

onUnmounted(() => {
  if (pollId) clearInterval(pollId)
  if (chipTimer) clearTimeout(chipTimer)
  if (resultTimer) clearTimeout(resultTimer)
  if (unsubPresence) unsubPresence()
  try {
    faceInst?.destroy?.()
  } catch {
    /* ignore */
  }
})
</script>

<style scoped>
.pet-root {
  position: fixed;
  right: 1.15rem;
  bottom: 5.75rem;
  z-index: 55;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.45rem;
}
.pet-bubble {
  max-width: 15.5rem;
  padding: 0.65rem 0.75rem;
  border-radius: 1rem 1rem 0.35rem 1rem;
  background: rgb(2 6 23 / 0.94);
  border: 1px solid rgba(94, 234, 212, 0.4);
  box-shadow: 0 12px 36px rgb(0 0 0 / 0.45);
  color: #e2e8f0;
}
.pet-result {
  max-width: 15.5rem;
  padding: 0.65rem 0.75rem;
  border-radius: 1rem 1rem 0.35rem 1rem;
  background: rgb(2 6 23 / 0.96);
  box-shadow: 0 12px 36px rgb(0 0 0 / 0.5);
  color: #e2e8f0;
}
.pet-result.is-ok {
  border: 1px solid rgba(16, 185, 129, 0.55);
}
.pet-result.is-warn {
  border: 1px solid rgba(251, 191, 36, 0.55);
}
.pet-result-label {
  margin: 0 0 0.25rem;
  font-size: 0.6rem;
  font-weight: 800;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #5eead4;
}
.pet-result.is-warn .pet-result-label {
  color: #fbbf24;
}
.pet-result-msg {
  margin: 0 0 0.45rem;
  font-size: 0.72rem;
  line-height: 1.35;
  color: #f1f5f9;
  font-family: ui-monospace, monospace;
}
.pet-bubble-msg {
  margin: 0;
  font-size: 0.75rem;
  line-height: 1.35;
}
.pet-bubble-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
  margin-top: 0.55rem;
}
.pet-btn-agir {
  font-size: 0.65rem;
  font-weight: 700;
  padding: 0.28rem 0.65rem;
  border-radius: 999px;
  border: none;
  background: #10b981;
  color: #022c22;
  cursor: pointer;
}
.pet-btn-agir:disabled {
  opacity: 0.5;
  cursor: default;
}
.pet-btn-later {
  font-size: 0.65rem;
  font-weight: 600;
  padding: 0.28rem 0.55rem;
  border-radius: 999px;
  background: transparent;
  color: #94a3b8;
  border: 1px solid rgba(255, 255, 255, 0.14);
  cursor: pointer;
}
.pet-hint {
  margin: 0.35rem 0 0;
  font-size: 0.58rem;
  font-family: ui-monospace, monospace;
  color: #64748b;
}
.pet-chip {
  font-size: 0.6rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: #99f6e4;
  background: rgb(2 6 23 / 0.85);
  border: 1px solid rgba(45, 212, 191, 0.35);
  border-radius: 999px;
  padding: 0.15rem 0.55rem;
}
.pet-avatar {
  position: relative;
  width: 4.5rem;
  height: 4.5rem;
  border-radius: 50%;
  border: 2px solid rgba(94, 234, 212, 0.35);
  background: radial-gradient(circle at 40% 30%, rgba(45, 212, 191, 0.18), rgb(2 6 23 / 0.92));
  box-shadow:
    0 0 0 3px rgba(15, 23, 42, 0.4),
    0 10px 28px rgb(0 0 0 / 0.5);
  overflow: hidden;
  cursor: pointer;
  animation: pet-bob 3.2s ease-in-out infinite;
  padding: 0;
}
.pet-avatar.alert {
  animation: pet-alert 0.9s ease-in-out 3;
  border-color: rgba(251, 191, 36, 0.65);
}
.pet-avatar.live {
  border-color: rgba(52, 211, 153, 0.75);
}
.pet-face {
  width: 100%;
  height: 100%;
  transform: scale(1.28) translateY(4%);
  transform-origin: center 35%;
}
.pet-face :deep(.face-rig-host) {
  max-width: none;
  margin: 0;
  width: 100%;
  height: 100%;
}
.pet-face :deep(.face-rig-stage) {
  border-radius: 50%;
  border: none;
  aspect-ratio: auto;
  height: 100%;
}
.pet-dot {
  position: absolute;
  right: 4px;
  bottom: 4px;
  width: 9px;
  height: 9px;
  border-radius: 50%;
  border: 1.5px solid rgb(2 6 23);
}
.dot-ok {
  background: #34d399;
}
.dot-warn {
  background: #fbbf24;
}
.dot-low {
  background: #f87171;
}
.dot-alert {
  background: #fbbf24;
  box-shadow: 0 0 8px rgba(251, 191, 36, 0.8);
}
@keyframes pet-bob {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-3px);
  }
}
@keyframes pet-alert {
  0%,
  100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.06);
  }
}
.pet-pop-enter-active,
.pet-pop-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.pet-pop-enter-from,
.pet-pop-leave-to {
  opacity: 0;
  transform: translateY(6px) scale(0.96);
}
</style>

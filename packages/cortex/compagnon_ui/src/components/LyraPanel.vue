<template>
  <div class="h-full flex flex-col">

    <header class="px-4 py-2 border-b border-slate-800 bg-slate-900/40 backdrop-blur">
      <h2 class="text-xs font-semibold tracking-wide uppercase">
        Lyra — Personnalisation
      </h2>
    </header>

    <div class="flex-1 px-4 py-3 space-y-4 text-xs overflow-y-auto">

      <!-- Face rig 2D — présence type desktop-pet -->
      <div
        id="lyra-face-host"
        ref="faceHost"
        class="face-rig-host mx-auto"
        :class="{ 'ring-2 ring-amber-400/50 rounded-full': !!initiative }"
        aria-label="Visage expressif Lyra"
      />
      <p class="text-[10px] text-slate-500 text-center leading-snug">
        Présence CSS (sheets collage gelés) · résultat Agir = bulle pet
      </p>

      <div
        v-if="initiative"
        class="rounded-xl border border-teal-400/35 bg-slate-950/80 p-2.5 space-y-2"
      >
        <p class="text-[10px] font-bold uppercase tracking-widest text-teal-300">Je vois</p>
        <p class="text-[11px] text-slate-200 leading-snug">{{ initiative.message }}</p>
        <button
          v-if="initiative.primary"
          type="button"
          class="w-full text-left rounded-lg border border-emerald-500/40 bg-emerald-500/15 px-2.5 py-1.5 text-[11px] font-semibold text-emerald-100 hover:bg-emerald-500/25 disabled:opacity-50"
          :disabled="proposing"
          @click="runInitiativeAgir"
        >
          {{ proposing ? '…' : initiative.primary.label }}
          <span
            v-if="initiative.primary.hint"
            class="block text-[9px] font-normal font-mono text-slate-500 mt-0.5"
          >{{ initiative.primary.hint }}</span>
        </button>
        <button
          type="button"
          class="text-[10px] text-slate-500 hover:text-slate-300"
          @click="dismiss"
        >Ignorer</button>
      </div>

      <!-- Jauges Lyra -->
      <div v-for="(value, key) in gauges" :key="key">
        <div class="flex justify-between items-center">
          <span class="opacity-80 capitalize">{{ key }}</span>
          <span class="font-semibold text-emerald-300">{{ value }}%</span>
        </div>
        <div class="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
          <div class="h-full bg-emerald-500/70" :style="{ width: value + '%' }"></div>
        </div>
      </div>

      <!-- Version -->
      <div class="flex justify-between items-center">
        <span class="opacity-80">Version</span>
        <span class="font-semibold">{{ version }}</span>
      </div>

      <!-- Latence -->
      <div class="flex justify-between items-center">
        <span class="opacity-80">Latence</span>
        <span class="font-semibold text-purple-300">{{ latency }} ms</span>
      </div>

      <!-- Uptime -->
      <div class="flex justify-between items-center">
        <span class="opacity-80">Uptime</span>
        <span class="font-semibold">{{ uptime }}</span>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { http } from '@/api/http'
import { useInitiative } from '@/composables/useInitiative'
import { useChat } from '@/composables/useChat'
import { proposeAction } from '@/lib/agir'

const gauges = ref({})
const version = ref("")
const latency = ref(0)
const uptime = ref("")
const faceHost = ref(null)

const { current: initiative, dismiss, proposing } = useInitiative()
const { addUserMessage, addMessage } = useChat()

async function runInitiativeAgir() {
  const intent = initiative.value?.primary
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
    dismiss(6, proposal ? 'accept' : 'dismiss')
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

let pollTimer = null
let faceReady = false

function moodFromGauges(g) {
  const e = Number(g?.energie ?? 50)
  const c = Number(g?.chaleur ?? 50)
  const p = Number(g?.patience ?? 50)
  if (c < 20) return 'tense'
  if (e < 25) return 'waiting'
  if (p < 30) return 'tense'
  if (e > 85 && c > 65) return 'curious'
  if (c > 75) return 'curious'
  return 'serene'
}

function expressionFromGauges(g) {
  const e = Number(g?.energie ?? 50)
  const c = Number(g?.chaleur ?? 50)
  const p = Number(g?.patience ?? 50)
  if (c < 20 || p < 25) return 'angry'
  if (e < 25) return 'sad'
  if (e > 85 && c > 70) return 'happy'
  if (c > 80) return 'surprised'
  return 'neutral'
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
  if (!window.FaceRig || !faceHost.value) return
  try {
    // Instance dédiée au panneau (ne vole pas le pet)
    if (typeof FaceRig.create === 'function') {
      const inst = FaceRig.create()
      await inst.init(faceHost.value, { characterId: 'lyra_assistant' })
      faceReady = !!inst.ready
      window.__lyraPanelFace = inst
    } else if (!FaceRig.ready) {
      await FaceRig.init(faceHost.value, { characterId: 'lyra_assistant' })
      faceReady = !!FaceRig.ready
    } else {
      faceReady = true
    }
  } catch (_) {
    faceReady = false
  }
}

function syncFace(g) {
  const face = window.__lyraPanelFace || (window.FaceRig?.ready ? window.FaceRig : null)
  if (!faceReady || !face) return
  try {
    face.setMood(moodFromGauges(g))
    face.setExpression(expressionFromGauges(g))
  } catch (_) {}
}

async function loadLyra() {
  try {
    const res = await http.get("/lyra/state")
    const data = res.data

    gauges.value = data.gauges || {}
    version.value = data.version
    latency.value = data.latency
    uptime.value = data.uptime_lyra || data.uptime
    syncFace(gauges.value)
  } catch (e) {
    console.warn("LyraPanel: Erreur de connexion au backend")
  }
}

onMounted(async () => {
  await initFace()
  await loadLyra()
  pollTimer = setInterval(loadLyra, 5000)
})

onBeforeUnmount(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<style scoped>
:global(html.light) header {
  background: rgba(255,255,255,0.6);
  color: #0f172a;
}

:global(html.light) span,
:global(html.light) h2 {
  color: #0f172a;
}

.face-rig-host {
  max-width: 9.5rem;
}
</style>

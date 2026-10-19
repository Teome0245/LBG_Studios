<template>
  <div class="h-full flex flex-col">

    <header class="px-4 py-2 border-b border-slate-800 bg-slate-900/40 backdrop-blur flex items-center justify-between">
      <h2 class="text-xs font-semibold tracking-wide uppercase">
        {{ avatarMode === 'vrm' ? 'Compagnon — Avatar 3D' : 'Lyra — Personnalisation' }}
      </h2>
      <span class="text-[10px] px-1.5 py-0.5 rounded font-mono" :class="avatarMode === 'vrm' ? 'bg-teal-500/15 text-teal-300' : 'bg-slate-800 text-slate-400'">
        {{ avatarMode === 'vrm' ? selectedModelLabel : '2D' }}
      </span>
    </header>

    <div class="flex-1 px-4 py-3 space-y-4 text-xs overflow-y-auto">

      <!-- Avatar Host (3D VRM ou 2D FaceRig) -->
      <div
        id="lyra-face-host"
        ref="faceHost"
        class="face-rig-host mx-auto"
        :class="[
          avatarMode === 'vrm' ? 'vrm-host' : '',
          { 'ring-2 ring-amber-400/50 rounded-full': !!initiative && avatarMode === 'face' }
        ]"
        :aria-label="avatarMode === 'vrm' ? 'Avatar 3D VRM' : 'Visage expressif Lyra'"
      />

      <p class="text-[10px] text-slate-500 text-center leading-snug">
        {{ avatarMode === 'vrm' ? 'Avatar 3D WebGL (Three.js / three-vrm) · lip-sync TTS actif' : 'Présence CSS (sheets collage gelés) · résultat Agir = bulle pet' }}
      </p>

      <!-- Sélecteur Mode & Modèle VRM -->
      <div class="space-y-2 pt-0.5">
        <div class="flex items-center justify-between text-[11px] bg-slate-950/60 p-1 rounded-lg border border-slate-800/80">
          <span class="text-slate-400 pl-1.5 font-medium">Mode</span>
          <div class="flex gap-1">
            <button
              type="button"
              class="px-2 py-0.5 rounded text-[10px] font-semibold transition"
              :class="avatarMode === 'vrm' ? 'bg-teal-500/25 text-teal-300 border border-teal-500/40 shadow-sm' : 'text-slate-400 hover:text-slate-200'"
              @click="setAvatarMode('vrm')"
            >
              3D VRM
            </button>
            <button
              type="button"
              class="px-2 py-0.5 rounded text-[10px] font-semibold transition"
              :class="avatarMode === 'face' ? 'bg-teal-500/25 text-teal-300 border border-teal-500/40 shadow-sm' : 'text-slate-400 hover:text-slate-200'"
              @click="setAvatarMode('face')"
            >
              2D Lyra
            </button>
          </div>
        </div>

        <!-- Poses expressives (si mode 3D VRM) -->
        <div v-if="avatarMode === 'vrm'" class="space-y-1.5 bg-slate-950/40 p-2 rounded-lg border border-slate-800/60">
          <div class="flex items-center justify-between text-[11px] pb-0.5">
            <span class="text-slate-400 font-medium">Modèle : <strong class="text-teal-300 font-normal">Compagnon</strong></span>
          </div>

          <!-- Poses expressives rapides -->
          <div class="grid grid-cols-4 gap-1 pt-1">
            <button
              type="button"
              class="py-1 rounded border border-slate-800 bg-slate-900/60 hover:bg-slate-800/80 text-[10px] text-slate-300 transition"
              title="Saluer"
              @click="triggerPose('wave', 2500)"
            >
              👋 Saluer
            </button>
            <button
              type="button"
              class="py-1 rounded border border-slate-800 bg-slate-900/60 hover:bg-slate-800/80 text-[10px] text-slate-300 transition"
              title="Réfléchir"
              @click="triggerPose('think', 4000)"
            >
              🤔 Réfléchir
            </button>
            <button
              type="button"
              class="py-1 rounded border border-slate-800 bg-slate-900/60 hover:bg-slate-800/80 text-[10px] text-slate-300 transition"
              title="Approuver"
              @click="triggerPose('approve', 3500)"
            >
              👍 Approuver
            </button>
            <button
              type="button"
              class="py-1 rounded border border-emerald-500/30 bg-emerald-950/30 hover:bg-emerald-900/50 text-[10px] text-emerald-200 transition"
              title="Bras croisés confiants"
              @click="triggerPose('crossArms', 5000)"
            >
              🦾 Confiante
            </button>
            <button
              type="button"
              class="py-1 rounded border border-pink-500/30 bg-pink-950/30 hover:bg-pink-900/50 text-[10px] text-pink-200 transition"
              title="Danse rythmée"
              @click="triggerPose('dance', 8000)"
            >
              💃 Danse
            </button>
            <button
              type="button"
              class="py-1 rounded border border-rose-500/30 bg-rose-950/30 hover:bg-rose-900/50 text-[10px] text-rose-200 transition"
              title="Bouderie / Colère"
              @click="triggerPose('angry', 4000)"
            >
              😤 Colère
            </button>
            <button
              type="button"
              class="py-1 rounded border border-cyan-500/30 bg-cyan-950/30 hover:bg-cyan-900/50 text-[10px] text-cyan-200 transition"
              title="Cycle de marche (VRMA)"
              @click="triggerPose('walk', 6000)"
            >
              🚶 Marche
            </button>
            <button
              type="button"
              class="py-1 rounded border border-indigo-500/30 bg-indigo-950/30 hover:bg-indigo-900/50 text-[10px] text-indigo-200 transition"
              title="Révérence polie"
              @click="triggerPose('bow', 3500)"
            >
              🙇 Révérence
            </button>
            <button
              type="button"
              class="py-1 rounded border border-teal-500/30 bg-teal-950/30 hover:bg-teal-900/50 text-[10px] text-teal-200 transition"
              title="Pose de repos posée (VRMA)"
              @click="triggerPose('relax', 6000)"
            >
              🧘 Repos
            </button>
            <button
              type="button"
              class="py-1 rounded border border-amber-500/30 bg-amber-950/30 hover:bg-amber-900/50 text-[10px] text-amber-200 transition"
              title="Observation vivante (VRMA)"
              @click="triggerPose('lookaround', 5000)"
            >
              👁️ Observer
            </button>
            <button
              type="button"
              class="py-1 rounded border border-purple-500/30 bg-purple-950/30 hover:bg-purple-900/50 text-[10px] text-purple-200 transition"
              title="Pirouette 360°"
              @click="triggerPose('spin', 4000)"
            >
              💫 Pirouette
            </button>
            <button
              type="button"
              class="py-1 rounded border border-yellow-500/30 bg-yellow-950/30 hover:bg-yellow-900/50 text-[10px] text-yellow-200 transition"
              title="Saut de joie / Victoire"
              @click="triggerPose('jump', 4000)"
            >
              🎉 Victoire
            </button>
            <button
              type="button"
              class="py-1 rounded border border-emerald-500/30 bg-emerald-950/30 hover:bg-emerald-900/50 text-[10px] text-emerald-200 transition"
              title="Étirement décontracté"
              @click="triggerPose('stretch', 5000)"
            >
              🙆‍♀️ Étirement
            </button>
            <button
              type="button"
              class="py-1 rounded border border-sky-500/30 bg-sky-950/30 hover:bg-sky-900/50 text-[10px] text-sky-200 transition"
              title="Applaudissements rythmés"
              @click="triggerPose('clapping', 4500)"
            >
              👏 Applaudir
            </button>
          </div>
        </div>
      </div>

      <div
        v-if="initiative"
        class="rounded-xl border border-teal-400/35 bg-slate-950/80 p-2.5 space-y-2"
      >
        <p class="text-[10px] font-bold uppercase tracking-widest text-teal-300">
          Je vois
          <span v-if="initiative.spontaneous" class="ml-1 text-sky-400/90 normal-case tracking-normal">· spontané</span>
        </p>
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
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { http } from '@/api/http'
import { useInitiative } from '@/composables/useInitiative'
import { useChat } from '@/composables/useChat'
import { proposeAction } from '@/lib/agir'

const gauges = ref({})
const version = ref("")
const latency = ref(0)
const uptime = ref("")
const faceHost = ref(null)

const avatarMode = ref(localStorage.getItem('compagnon_avatar_mode') || 'vrm')
const selectedModel = ref(localStorage.getItem('compagnon_vrm_model') || 'Compagnon.vrm')
const vrmFraming = ref('bust')
const availableModels = [
  { id: 'Compagnon.vrm', label: 'Compagnon' },
  { id: 'Anna.vrm', label: 'Anna' },
  { id: 'Aurora.vrm', label: 'Aurora' },
  { id: 'LadyKoi.vrm', label: 'LadyKoi' },
]

const selectedModelLabel = computed(() => {
  const hit = availableModels.find((m) => m.id === selectedModel.value)
  return hit ? hit.label : 'VRM'
})

let vrmInst = null
let faceInst = null
let faceReady = false

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

function ensureVrmAssets() {
  return new Promise((resolve) => {
    if (window.__createVrmPet) {
      resolve()
      return
    }
    const existing = document.getElementById('vrm-pet-bundle-js')
    if (existing) {
      existing.addEventListener('load', () => resolve(), { once: true })
      if (window.__createVrmPet) resolve()
      return
    }
    const script = document.createElement('script')
    script.id = 'vrm-pet-bundle-js'
    script.src = '/vrm/vrm_pet.bundle.js?v=chibi_v3'
    script.onload = () => resolve()
    script.onerror = () => resolve()
    document.body.appendChild(script)
  })
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

async function initVrm() {
  await ensureVrmAssets()
  await nextTick()
  if (!faceHost.value || !window.__createVrmPet) return
  if (vrmInst?.destroy) {
    try {
      vrmInst.destroy()
    } catch (_) {}
    vrmInst = null
  }
  faceHost.value.innerHTML = ''
  try {
    vrmInst = window.__createVrmPet(faceHost.value, {
      modelUrl: '/vrm/' + selectedModel.value,
      framing: vrmFraming.value,
    })
    window.__lyraPanelFace = vrmInst
    window.__vrmPetInstance = vrmInst
    faceReady = true
    syncFace(gauges.value)
  } catch (e) {
    console.warn('[LyraPanel] VRM init error', e)
    faceReady = false
  }
}

async function initFace() {
  await ensureFaceAssets()
  await nextTick()
  if (!window.FaceRig || !faceHost.value) return
  try {
    if (typeof FaceRig.create === 'function') {
      faceInst = FaceRig.create()
      await faceInst.init(faceHost.value, { characterId: 'lyra_assistant' })
      faceReady = !!faceInst.ready
      window.__lyraPanelFace = faceInst
      window.__vrmPetInstance = null
    } else if (!FaceRig.ready) {
      await FaceRig.init(faceHost.value, { characterId: 'lyra_assistant' })
      faceReady = !!FaceRig.ready
      faceInst = FaceRig
    } else {
      faceReady = true
      faceInst = FaceRig
    }
  } catch (_) {
    faceReady = false
  }
}

async function switchAvatar() {
  if (vrmInst?.destroy) {
    try {
      vrmInst.destroy()
    } catch (_) {}
    vrmInst = null
  }
  if (faceInst?.destroy) {
    try {
      faceInst.destroy()
    } catch (_) {}
    faceInst = null
  }
  window.__lyraPanelFace = null
  window.__vrmPetInstance = null
  faceReady = false
  if (faceHost.value) faceHost.value.innerHTML = ''

  if (avatarMode.value === 'vrm') {
    await initVrm()
  } else {
    await initFace()
  }
}

function setAvatarMode(mode) {
  if (avatarMode.value === mode) return
  avatarMode.value = mode
  try {
    localStorage.setItem('compagnon_avatar_mode', mode)
  } catch (_) {}
  switchAvatar()
}

function onModelChange() {
  try {
    localStorage.setItem('compagnon_vrm_model', selectedModel.value)
  } catch (_) {}
  if (avatarMode.value === 'vrm') {
    switchAvatar()
  }
}

function triggerPose(pose, holdMs) {
  // 1. Anime la vue locale (buste WebGL)
  if (vrmInst?.setPose) {
    vrmInst.setPose(pose, holdMs)
  }
  // 2. Transmet instantanément l'action au Desktop Pet (modèle du bureau Windows)
  try {
    if (window.compagnonDesktop && typeof window.compagnonDesktop.setPose === 'function') {
      window.compagnonDesktop.setPose(pose, holdMs)
    } else {
      fetch('http://127.0.0.1:8765/avatar/command', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cmd: 'set_pose', pose, holdMs }),
      }).catch(() => {})
    }
  } catch (_) {}
}

function syncFace(g) {
  if (!faceReady) return
  if (avatarMode.value === 'vrm' && vrmInst) {
    try {
      vrmInst.setMood(moodFromGauges(g))
    } catch (_) {}
    return
  }
  const face = window.__lyraPanelFace || (window.FaceRig?.ready ? window.FaceRig : null)
  if (!face) return
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
  await switchAvatar()
  await loadLyra()
  pollTimer = setInterval(loadLyra, 5000)
})

onBeforeUnmount(() => {
  if (pollTimer) clearInterval(pollTimer)
  if (vrmInst?.destroy) {
    try {
      vrmInst.destroy()
    } catch (_) {}
    vrmInst = null
  }
  window.__lyraPanelFace = null
  window.__vrmPetInstance = null
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

.vrm-host {
  width: 100% !important;
  max-width: 13.5rem !important;
  height: 220px !important;
  border-radius: 1rem;
  overflow: hidden;
  background: radial-gradient(circle at 50% 30%, rgba(30, 41, 59, 0.75) 0%, rgba(2, 6, 23, 0.95) 100%);
  border: 1px solid rgba(51, 65, 85, 0.65);
  box-shadow: inset 0 2px 10px rgba(0, 0, 0, 0.7);
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

:deep(.vrm-host canvas) {
  width: 100% !important;
  height: 100% !important;
  display: block;
}
</style>

<template>
  <div class="h-full flex flex-col">

    <header class="px-4 py-2 border-b border-slate-800 bg-slate-900/40 backdrop-blur flex items-center justify-between flex-shrink-0">
      <h2 class="text-xs font-semibold tracking-wide uppercase">
        {{ avatarMode === 'vrm' ? 'Compagnon — Avatar 3D' : 'Lyra — Personnalisation' }}
      </h2>
      <div class="flex items-center gap-1.5">
        <button
          type="button"
          class="px-2 py-0.5 rounded text-[10px] font-medium bg-cyan-950/60 hover:bg-cyan-900/80 border border-cyan-500/40 text-cyan-300 flex items-center gap-1 transition shadow-sm"
          title="Vérifier et synchroniser les mises à jour (A: -> Windows C:)"
          @click="triggerUpdate"
        >
          <span :class="isUpdating ? 'animate-spin' : ''">🔄</span>
          <span>{{ isUpdating ? 'Sync...' : 'MAJ' }}</span>
        </button>
        <span class="text-[10px] px-1.5 py-0.5 rounded font-mono" :class="avatarMode === 'vrm' ? 'bg-teal-500/15 text-teal-300' : 'bg-slate-800 text-slate-400'">
          {{ avatarMode === 'vrm' ? selectedModelLabel : '2D' }}
        </span>
      </div>
    </header>

    <!-- Zone Avatar 3D / 2D fixe (ne défile pas, toujours visible quand on clique sur les danses/poses) -->
    <div class="px-4 pt-2.5 pb-1 border-b border-slate-800/80 bg-slate-950/20 flex-shrink-0">
      <!-- Avatar Host (3D VRM ou 2D FaceRig) -->
      <div
        id="lyra-face-host"
        ref="faceHost"
        class="face-rig-host mx-auto transition-all duration-300"
        :class="[
          avatarMode === 'vrm' ? 'vrm-host' : '',
          vrmFraming === 'full' && avatarMode === 'vrm' ? 'framing-full-host' : '',
          { 'ring-2 ring-amber-400/50 rounded-full': !!initiative && avatarMode === 'face' }
        ]"
        :aria-label="avatarMode === 'vrm' ? 'Avatar 3D VRM' : 'Visage expressif Lyra'"
      />

      <p class="text-[10px] text-slate-500 text-center leading-snug pt-1">
        {{ avatarMode === 'vrm' ? (vrmFraming === 'full' ? 'Avatar 3D WebGL · Corps entier (danses & marche)' : 'Avatar 3D WebGL (Three.js / three-vrm) · lip-sync TTS actif') : 'Présence CSS (sheets collage gelés) · résultat Agir = bulle pet' }}
      </p>
    </div>

    <div class="flex-1 px-4 py-3 space-y-4 text-xs overflow-y-auto">

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
            <div class="flex items-center gap-1">
              <button
                type="button"
                :class="vrmFraming === 'bust' ? 'bg-teal-600/40 text-teal-200 border-teal-500/50' : 'bg-slate-900/60 text-slate-400 border-slate-800'"
                class="px-1.5 py-0.5 rounded text-[10px] border transition"
                title="Cadrage portrait / buste"
                @click="toggleFraming('bust')"
              >
                Buste
              </button>
              <button
                type="button"
                :class="vrmFraming === 'full' ? 'bg-teal-600/40 text-teal-200 border-teal-500/50' : 'bg-slate-900/60 text-slate-400 border-slate-800'"
                class="px-1.5 py-0.5 rounded text-[10px] border transition"
                title="Cadrage corps entier (danses & marche)"
                @click="toggleFraming('full')"
              >
                Corps
              </button>
            </div>
          </div>

          <!-- Accessoires 3D VRM Modulaires (Priorité Haute, immédiatement visibles) -->
          <div class="pt-2 pb-1 border-t border-cyan-500/30">
            <div class="flex items-center justify-between text-[11px] pb-1.5">
              <span class="text-cyan-300 font-semibold flex items-center gap-1.5">
                <span>👓</span>
                <span>Accessoires 3D</span>
              </span>
              <span class="text-[9px] text-cyan-400/80 font-mono bg-cyan-950/80 px-1.5 py-0.5 rounded border border-cyan-500/30">Modulaires · GLB</span>
            </div>
            <div class="grid grid-cols-3 gap-1.5">
              <button
                type="button"
                class="py-1.5 px-1 rounded border text-[10px] transition font-medium flex items-center justify-center gap-1 cursor-pointer"
                :class="activeAccessories.has('visor') ? 'border-cyan-400 bg-cyan-900/80 text-cyan-200 shadow-md shadow-cyan-500/20 ring-1 ring-cyan-400/50' : 'border-slate-700/60 bg-slate-900/50 text-slate-300 hover:text-white hover:border-slate-500'"
                title="Visière HUD cybernétique sur la tête"
                @click="triggerAccessory('visor')"
              >
                <span>🕶️</span>
                <span>Visière</span>
              </button>
              <button
                type="button"
                class="py-1.5 px-1 rounded border text-[10px] transition font-medium flex items-center justify-center gap-1 cursor-pointer"
                :class="activeAccessories.has('datapad') ? 'border-teal-400 bg-teal-900/80 text-teal-200 shadow-md shadow-teal-500/20 ring-1 ring-teal-400/50' : 'border-slate-700/60 bg-slate-900/50 text-slate-300 hover:text-white hover:border-slate-500'"
                title="Datapad holographique en main"
                @click="triggerAccessory('datapad')"
              >
                <span>📱</span>
                <span>Datapad</span>
              </button>
              <button
                type="button"
                class="py-1.5 px-1 rounded border text-[10px] transition font-medium flex items-center justify-center gap-1 cursor-pointer"
                :class="activeAccessories.has('headset') ? 'border-pink-400 bg-pink-900/80 text-pink-200 shadow-md shadow-pink-500/20 ring-1 ring-pink-400/50' : 'border-slate-700/60 bg-slate-900/50 text-slate-300 hover:text-white hover:border-slate-500'"
                title="Oreillette de communication neurale"
                @click="triggerAccessory('headset')"
              >
                <span>🎧</span>
                <span>Oreillette</span>
              </button>
            </div>
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
            <button
              type="button"
              class="py-1 rounded border border-cyan-500/30 bg-cyan-950/30 hover:bg-cyan-900/50 text-[10px] text-cyan-200 transition font-medium"
              title="Posture de concentration et scan de code"
              @click="triggerPose('focus', 6000)"
            >
              🔍 Focus
            </button>
          </div>

          <!-- Pack Danses VRM -->
          <div class="pt-2 border-t border-slate-800/80">
            <div class="flex items-center justify-between text-[11px] pb-1">
              <span class="text-pink-300 font-medium flex items-center gap-1">💃 Pack Danses</span>
              <span class="text-[9px] text-slate-500 font-mono">VRMA / Kinematic 60fps</span>
            </div>
            <div class="grid grid-cols-4 gap-1">
              <button
                type="button"
                class="py-1 rounded border border-rose-500/40 bg-rose-950/40 hover:bg-rose-900/60 text-[10px] text-rose-200 transition font-medium"
                title="Petite danse Idol K-Pop avec Finger Heart et cyber-cœurs"
                @click="triggerPose('fingerHeart', 8500)"
              >
                💖 Mini Heart
              </button>
              <button
                type="button"
                class="py-1 rounded border border-pink-500/30 bg-pink-950/30 hover:bg-pink-900/50 text-[10px] text-pink-200 transition"
                title="Danse Groove fluide & détendue"
                @click="triggerPose('dance', 8000)"
              >
                🎵 Groove
              </button>
              <button
                type="button"
                class="py-1 rounded border border-rose-500/30 bg-rose-950/30 hover:bg-rose-900/50 text-[10px] text-rose-200 transition"
                title="Samba / Salsa latino avec déhanché en huit"
                @click="triggerPose('samba', 8000)"
              >
                💃 Samba
              </button>
              <button
                type="button"
                class="py-1 rounded border border-orange-500/30 bg-orange-950/30 hover:bg-orange-900/50 text-[10px] text-orange-200 transition"
                title="Hip-Hop / Street Bounce athlétique"
                @click="triggerPose('hiphop', 8000)"
              >
                🧢 Hip-Hop
              </button>
              <button
                type="button"
                class="py-1 rounded border border-cyan-500/30 bg-cyan-950/30 hover:bg-cyan-900/50 text-[10px] text-cyan-200 transition"
                title="Robot / Popping avec onde cinématique"
                @click="triggerPose('robot', 8000)"
              >
                🤖 Robot
              </button>
              <button
                type="button"
                class="py-1 rounded border border-amber-500/30 bg-amber-950/30 hover:bg-amber-900/50 text-[10px] text-amber-200 transition"
                title="Disco Fever 70s avec bras vers le ciel"
                @click="triggerPose('disco', 8000)"
              >
                🪩 Disco
              </button>
              <button
                type="button"
                class="py-1 rounded border border-purple-500/30 bg-purple-950/30 hover:bg-purple-900/50 text-[10px] text-purple-200 transition"
                title="Pirouette 360° continue gracieuse"
                @click="triggerPose('spin', 6000)"
              >
                💫 Pirouette
              </button>
            </div>
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
import { ref, computed, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import { http } from '@/api/http'
import { useInitiative } from '@/composables/useInitiative'
import { useChat } from '@/composables/useChat'
import { proposeAction } from '@/lib/agir'

const gauges = ref({})
const version = ref("")
const latency = ref(0)
const uptime = ref("")
const faceHost = ref(null)

const isUpdating = ref(false)
const activeAccessories = ref(new Set())

function triggerAccessory(type) {
  if (activeAccessories.value.has(type)) {
    activeAccessories.value.delete(type)
  } else {
    activeAccessories.value.add(type)
  }
  try {
    if (window.compagnonDesktop && typeof window.compagnonDesktop.toggleAccessory === 'function') {
      window.compagnonDesktop.toggleAccessory(type)
    } else {
      fetch('http://127.0.0.1:8765/avatar/command', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cmd: 'toggle_accessory', type }),
      }).catch(() => {})
    }
  } catch (_) {}
}

async function triggerUpdate() {
  isUpdating.value = true
  try {
    if (window.compagnonDesktop && typeof window.compagnonDesktop.checkUpdates === 'function') {
      window.compagnonDesktop.checkUpdates()
    } else {
      await fetch('http://127.0.0.1:8765/avatar/command', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cmd: 'check_update' }),
      }).catch(() => {})
    }
  } catch (_) {
  } finally {
    setTimeout(() => {
      isUpdating.value = false
    }, 2500)
  }
}

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
const { addUserMessage, addMessage, messages } = useChat()

// Réaction vivante et synchronisation de parole avec le Chat
watch(
  () => (messages.value ? messages.value.length : 0),
  (newLen, oldLen) => {
    if (newLen > oldLen && newLen > 0 && messages.value) {
      const last = messages.value[newLen - 1]
      if (last && last.role === 'assistant' && last.content) {
        onAssistantReply(last.content)
      }
    }
  }
)

function onAssistantReply(text) {
  const t = String(text).toLowerCase()
  if (vrmInst && typeof vrmInst.say === 'function') {
    vrmInst.say(text)
  }
  // Détection expressive spontanée selon le ton du dialogue
  if (t.includes('bonjour') || t.includes('salut') || t.includes('coucou') || t.includes('quoi de neuf')) {
    triggerPose('wave', 3000)
  } else if (t.includes('réfléch') || t.includes('analys') || t.includes('voyons') || t.includes('vérifi') || t.includes('propose')) {
    triggerPose('think', 4000)
  } else if (t.includes('parfait') || t.includes('d\'accord') || t.includes('validé') || t.includes('super')) {
    triggerPose('approve', 3500)
  } else if (t.includes('attention') || t.includes('alerte') || t.includes('danger') || t.includes('piège')) {
    triggerPose('crossArms', 4500)
  }
}

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
    script.src = '/vrm/vrm_pet.bundle.js?v=finger_heart_v6'
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

function toggleFraming(f) {
  vrmFraming.value = f
  if (vrmInst?.setFraming) {
    vrmInst.setFraming(f)
  }
}

let returnToBustTimer = null

function triggerPose(pose, holdMs) {
  const fullBodyPoses = ['dance', 'danse', 'samba', 'salsa', 'hiphop', 'walk', 'marche', 'spin', 'jump', 'disco', 'robot', 'twist', 'popping', 'fever']
  const isFullBody = fullBodyPoses.includes(String(pose || '').toLowerCase())

  if (returnToBustTimer) {
    clearTimeout(returnToBustTimer)
    returnToBustTimer = null
  }

  // Si on est en cadrage buste et qu'une danse démarre : zoom arrière pour voir le corps entier, puis retour en buste
  if (isFullBody && vrmFraming.value === 'bust') {
    vrmFraming.value = 'full'
    if (vrmInst?.setFraming) {
      vrmInst.setFraming('full')
    }
    const duration = (Number(holdMs) > 0) ? Number(holdMs) : 8000
    returnToBustTimer = setTimeout(() => {
      vrmFraming.value = 'bust'
      if (vrmInst?.setFraming) {
        vrmInst.setFraming('bust')
      }
      returnToBustTimer = null
    }, duration + 350)
  }

  // 1. Anime la vue locale (buste ou corps WebGL)
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
  if (returnToBustTimer) clearTimeout(returnToBustTimer)
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
  transition: height 0.3s cubic-bezier(0.16, 1, 0.3, 1), max-width 0.3s ease;
}

.vrm-host.framing-full-host {
  height: 285px !important;
  max-width: 15rem !important;
}

:deep(.vrm-host canvas) {
  width: 100% !important;
  height: 100% !important;
  display: block;
}
</style>

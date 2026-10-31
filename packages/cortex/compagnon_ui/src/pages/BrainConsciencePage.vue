<script setup>
import { reactive, ref, onMounted, onUnmounted } from 'vue'
import { http } from '@/api/http'
import NavRail from '../components/NavRail.vue'
import ChatHeader from '../components/ChatHeader.vue'
import LyraConscience3D from '../components/lyra/LyraConscience3D.vue'

const state = reactive({
  gauges: {
    chaleur: 75,
    energie: 70,
    patience: 80,
    confiance: 75
  },
  uptime_backend: '',
  uptime_lyra: '',
  version: '',
  latency: null,
  style: 'chaleureuse'
})

const pollTimer = ref(null)
const history = ref([])

function addHistory(msg) {
  const ts = new Date().toLocaleTimeString('fr-FR', { hour12: false })
  history.value.unshift({ ts, msg })
  if (history.value.length > 30) history.value.pop()
}

async function fetchState() {
  try {
    const res = await http.get('/lyra/state')
    const data = res.data
    if (data && data.gauges) {
      state.gauges.chaleur = data.gauges.chaleur
      state.gauges.energie = data.gauges.energie
      state.gauges.patience = data.gauges.patience
      state.gauges.confiance = data.gauges.confiance
    }
    state.uptime_backend = data.uptime_backend || ''
    state.uptime_lyra = data.uptime_lyra || ''
    state.version = data.version || ''
    state.latency = data.latency || null
    state.style = data.style || 'chaleureuse'
  } catch (e) {
    // console.warn('Lyra state fetch error:', e)
  }
}

async function updateGauge(gaugeKey, delta) {
  try {
    const res = await http.post('/lyra/update', {
      gauge: gaugeKey,
      delta
    })
    const data = res.data
    if (data && data.gauges) {
      state.gauges.chaleur = data.gauges.chaleur
      state.gauges.energie = data.gauges.energie
      state.gauges.patience = data.gauges.patience
      state.gauges.confiance = data.gauges.confiance
    }
    addHistory(`${gaugeKey} ${delta > 0 ? '+' : ''}${delta}%`)
  } catch (e) {
    addHistory(`Erreur maj ${gaugeKey}`)
  }
}

function onSliderChange(gaugeKey, event) {
  const newVal = Number(event.target.value)
  const current = state.gauges[gaugeKey] || 0
  const delta = newVal - current
  if (delta !== 0) {
    updateGauge(gaugeKey, delta)
  }
}

function applyPreset(name) {
  const targets = {
    chaleureuse: { chaleur: 95, energie: 80, patience: 85, confiance: 80 },
    creative: { chaleur: 85, energie: 95, patience: 70, confiance: 90 },
    neutre: { chaleur: 50, energie: 50, patience: 60, confiance: 60 },
    froide: { chaleur: 20, energie: 35, patience: 40, confiance: 40 }
  }
  const target = targets[name]
  if (target) {
    Object.keys(target).forEach(key => {
      const delta = target[key] - state.gauges[key]
      if (delta !== 0) {
        updateGauge(key, delta)
      }
    })
    addHistory(`Preset appliqué : ${name}`)
  }
}

onMounted(() => {
  fetchState()
  pollTimer.value = setInterval(fetchState, 5000)
})

onUnmounted(() => {
  if (pollTimer.value) clearInterval(pollTimer.value)
})
</script>

<template>
  <div class="flex h-full w-full overflow-hidden bg-slate-950 text-slate-200">
    <!-- Navigation Rail -->
    <NavRail />

    <div class="flex-1 flex flex-col relative min-w-0">
      <ChatHeader />

      <main class="flex-1 p-6 overflow-hidden flex flex-col gap-6">
        
        <!-- Header -->
        <div class="flex items-center justify-between">
          <div>
            <div class="flex items-center gap-3">
              <h1 class="text-2xl font-bold font-outfit text-white">Conscience Holographique de Lyra</h1>
              <span class="px-2.5 py-0.5 rounded-full text-[11px] font-mono uppercase bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                Temps Réel · 3D
              </span>
            </div>
            <p class="text-xs text-slate-400 mt-1">
              Visualisation synaptique des états internes et des flux cognitifs du Compagnon IA.
            </p>
          </div>

          <div class="flex items-center gap-2">
            <button
              @click="applyPreset('chaleureuse')"
              class="px-3 py-1.5 text-xs rounded-xl bg-amber-500/15 text-amber-300 border border-amber-500/30 hover:bg-amber-500/25 transition-all"
            >
              🔥 Chaleureuse
            </button>
            <button
              @click="applyPreset('creative')"
              class="px-3 py-1.5 text-xs rounded-xl bg-cyan-500/15 text-cyan-300 border border-cyan-500/30 hover:bg-cyan-500/25 transition-all"
            >
              ⚡ Créative
            </button>
            <button
              @click="applyPreset('neutre')"
              class="px-3 py-1.5 text-xs rounded-xl bg-slate-800 text-slate-300 border border-white/10 hover:bg-slate-700 transition-all"
            >
              ⚖️ Neutre
            </button>
            <button
              @click="applyPreset('froide')"
              class="px-3 py-1.5 text-xs rounded-xl bg-rose-500/15 text-rose-300 border border-rose-500/30 hover:bg-rose-500/25 transition-all"
            >
              ❄️ Concise
            </button>
          </div>
        </div>

        <!-- Main Viewport + Live Dials -->
        <div class="flex-1 grid grid-cols-1 lg:grid-cols-4 gap-6 min-h-0">
          
          <!-- 3D Canvas Box (3 colonnes) -->
          <div class="lg:col-span-3 h-full rounded-3xl overflow-hidden relative shadow-2xl">
            <LyraConscience3D
              :gauges="state.gauges"
              :style-mode="state.style"
              :interactive="true"
            />
          </div>

          <!-- Panneau Latéral : Réglages direct des jauges & Log (1 colonne) -->
          <div class="glass-panel p-5 rounded-3xl border border-white/5 flex flex-col gap-6 overflow-y-auto scrollbar-custom">
            <div>
              <h2 class="text-sm font-bold uppercase tracking-wider text-slate-300 font-outfit mb-4">
                Piliers Cognitifs
              </h2>

              <div class="space-y-4">
                <!-- Chaleur -->
                <div class="space-y-1.5">
                  <div class="flex justify-between text-xs">
                    <span class="text-amber-400 font-medium">🔥 Chaleur</span>
                    <span class="font-mono text-white">{{ state.gauges.chaleur }}%</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    :value="state.gauges.chaleur"
                    @input="onSliderChange('chaleur', $event)"
                    class="w-full h-1.5 bg-white/10 rounded-lg appearance-none cursor-pointer accent-amber-500"
                  />
                </div>

                <!-- Énergie -->
                <div class="space-y-1.5">
                  <div class="flex justify-between text-xs">
                    <span class="text-cyan-400 font-medium">⚡ Énergie</span>
                    <span class="font-mono text-white">{{ state.gauges.energie }}%</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    :value="state.gauges.energie"
                    @input="onSliderChange('energie', $event)"
                    class="w-full h-1.5 bg-white/10 rounded-lg appearance-none cursor-pointer accent-cyan-500"
                  />
                </div>

                <!-- Patience -->
                <div class="space-y-1.5">
                  <div class="flex justify-between text-xs">
                    <span class="text-emerald-400 font-medium">🧘 Patience</span>
                    <span class="font-mono text-white">{{ state.gauges.patience }}%</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    :value="state.gauges.patience"
                    @input="onSliderChange('patience', $event)"
                    class="w-full h-1.5 bg-white/10 rounded-lg appearance-none cursor-pointer accent-emerald-500"
                  />
                </div>

                <!-- Confiance -->
                <div class="space-y-1.5">
                  <div class="flex justify-between text-xs">
                    <span class="text-violet-400 font-medium">⭐ Confiance</span>
                    <span class="font-mono text-white">{{ state.gauges.confiance }}%</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    :value="state.gauges.confiance"
                    @input="onSliderChange('confiance', $event)"
                    class="w-full h-1.5 bg-white/10 rounded-lg appearance-none cursor-pointer accent-violet-500"
                  />
                </div>
              </div>
            </div>

            <!-- État Système & Métriques -->
            <div class="border-t border-white/5 pt-4">
              <h3 class="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
                Métriques Compagnon
              </h3>
              <div class="space-y-1.5 text-xs text-slate-300 font-mono">
                <div class="flex justify-between">
                  <span class="text-slate-500">Style actif :</span>
                  <span class="text-emerald-400 capitalize">{{ state.style }}</span>
                </div>
                <div class="flex justify-between" v-if="state.latency">
                  <span class="text-slate-500">Latence :</span>
                  <span>{{ state.latency }} ms</span>
                </div>
                <div class="flex justify-between" v-if="state.uptime_lyra">
                  <span class="text-slate-500">Uptime Lyra :</span>
                  <span>{{ state.uptime_lyra }}</span>
                </div>
              </div>
            </div>

            <!-- Historique des impulsions -->
            <div class="border-t border-white/5 pt-4 flex-1 flex flex-col min-h-[120px]">
              <h3 class="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
                Historique Cognitif
              </h3>
              <div class="flex-1 overflow-y-auto space-y-1.5 text-[11px] font-mono text-slate-400 scrollbar-custom max-h-40">
                <div v-for="(h, idx) in history" :key="idx" class="flex items-center gap-2">
                  <span class="text-slate-600">{{ h.ts }}</span>
                  <span class="text-slate-300">{{ h.msg }}</span>
                </div>
                <div v-if="history.length === 0" class="text-slate-600 italic">
                  Aucun ajustement récent
                </div>
              </div>
            </div>

          </div>

        </div>

      </main>
    </div>
  </div>
</template>


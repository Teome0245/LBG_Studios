<template>
  <!-- Avatar Lyra discret — coin bas-droit, expand on click -->
  <div class="fixed bottom-6 right-6 z-50 flex flex-col items-end gap-2 pointer-events-none">
    <!-- Popover jauges (ouvert) -->
    <div
      v-if="!lyraMinimized"
      class="pointer-events-auto w-56 rounded-2xl border border-white/15 bg-slate-950/95 backdrop-blur-md shadow-2xl p-3 animate-slide-up"
    >
      <div class="flex items-center justify-between mb-2">
        <span class="text-[10px] font-bold uppercase tracking-widest text-slate-400">Lyra</span>
        <div class="flex gap-1">
          <router-link
            to="/lyra"
            class="text-[10px] text-cyan-400/90 hover:text-cyan-300 px-1"
            title="Lyra Advanced"
          >↗</router-link>
          <button
            type="button"
            class="text-slate-500 hover:text-white text-[10px] px-1"
            title="Réduire"
            @click="toggleLyra"
          >✕</button>
        </div>
      </div>
      <div class="grid grid-cols-4 gap-2">
        <div v-for="g in gaugeList" :key="g.key" class="flex flex-col items-center">
          <span class="text-[9px] text-slate-500 mb-0.5">{{ g.short }}</span>
          <div class="w-1.5 h-8 bg-slate-800 rounded-full overflow-hidden relative">
            <div
              class="absolute bottom-0 left-0 w-full transition-all duration-500"
              :style="{
                height: (gauges?.[g.key] ?? 0) + '%',
                backgroundColor: gaugeColor(gauges?.[g.key] ?? 0),
              }"
            />
          </div>
          <span class="text-[8px] font-mono text-slate-500 mt-0.5">{{ gauges?.[g.key] ?? 0 }}</span>
          <div class="flex gap-0.5 mt-0.5">
            <button
              type="button"
              class="text-[8px] text-slate-500 hover:text-white px-0.5"
              @click="updateGauge(g.key, +5)"
            >+</button>
            <button
              type="button"
              class="text-[8px] text-slate-500 hover:text-white px-0.5"
              @click="updateGauge(g.key, -5)"
            >−</button>
          </div>
        </div>
      </div>
      <p class="text-[8px] text-slate-600 mt-2 font-mono truncate">{{ uptime_lyra }}</p>
    </div>

    <!-- Bouton avatar -->
    <button
      type="button"
      class="pointer-events-auto h-12 w-12 rounded-2xl border border-white/20 bg-slate-900/90 shadow-xl flex items-center justify-center overflow-hidden ring-2 transition-all hover:scale-105 active:scale-95"
      :class="moodRing"
      :title="lyraMinimized ? 'Ouvrir Lyra' : 'Lyra ouverte'"
      @click="toggleLyra"
    >
      <img
        :src="avatarSrc"
        alt="Lyra"
        class="h-full w-full object-cover"
        @error="onImgError"
      />
    </button>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { http } from '@/api/http'
import { useLayout } from '../composables/useLayout'

const { lyraMinimized, toggleLyra } = useLayout()

const gauges = ref({
  chaleur: 50,
  energie: 50,
  patience: 50,
  confiance: 50,
})
const uptime_lyra = ref('—')
const imgBroken = ref(false)

const gaugeList = [
  { key: 'chaleur', short: 'ch' },
  { key: 'energie', short: 'én' },
  { key: 'patience', short: 'pa' },
  { key: 'confiance', short: 'co' },
]

const energy = computed(() => Number(gauges.value?.energie) || 50)

const moodRing = computed(() => {
  if (energy.value > 70) return 'ring-emerald-500/50'
  if (energy.value > 40) return 'ring-amber-500/40'
  return 'ring-rose-500/40'
})

const avatarSrc = computed(() => {
  if (imgBroken.value) {
    return 'https://ui-avatars.com/api/?name=L&background=0f172a&color=34d399&size=96'
  }
  if (energy.value > 70) return '/assets/icons/256/orchestrateur_happy.png'
  if (energy.value > 40) return '/assets/icons/256/orchestrateur_happy.png'
  return '/assets/icons/256/orchestrateur_happy.png'
})

function onImgError() {
  imgBroken.value = true
}

function gaugeColor(v) {
  if (v > 70) return '#4ade80'
  if (v > 40) return '#facc15'
  return '#f87171'
}

async function fetchState() {
  try {
    const res = await http.get('/lyra/state')
    if (res.data?.gauges) {
      gauges.value = res.data.gauges
      uptime_lyra.value = res.data.uptime_lyra || '—'
    }
  } catch {
    /* offline ok */
  }
}

async function updateGauge(gauge, delta) {
  try {
    await http.post('/lyra/update', { gauge, delta })
    fetchState()
  } catch (e) {
    console.error('Lyra update:', e)
  }
}

let intervalId
onMounted(() => {
  fetchState()
  intervalId = setInterval(fetchState, 8000)
})
onUnmounted(() => {
  if (intervalId) clearInterval(intervalId)
})
</script>

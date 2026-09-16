<script setup>
import { reactive, ref, onMounted } from "vue";
import { http } from "@/api/http";
import Sidebar from "../components/Sidebar.vue";
import ChatHeader from "../components/ChatHeader.vue";
import LyraGauge from "../components/lyra/LyraGauge.vue";
import LyraStylePreview from "../components/lyra/LyraStylePreview.vue";
import LyraHistory from "../components/lyra/LyraHistory.vue";

const state = reactive({
  gauges: {
    chaleur: 0,
    energie: 0,
    patience: 0,
    confiance: 0
  },
  uptime_backend: "",
  uptime_lyra: "",
  version: "",
  latency: null,
  style: ""
});

const gauges = state.gauges;

const gaugeLabels = {
  chaleur: "Chaleur",
  energie: "Énergie",
  patience: "Patience",
  confiance: "Confiance"
};

const history = ref([]);

function addHistory(message) {
  const now = new Date();
  const ts = now.toLocaleTimeString("fr-FR", { hour12: false });
  history.value.unshift({
    timestamp: ts,
    message
  });
  if (history.value.length > 50) {
    history.value.pop();
  }
}

async function fetchState() {
  try {
    const res = await http.get("/lyra/state");
    const data = res.data;

    state.gauges.chaleur = data.gauges.chaleur;
    state.gauges.energie = data.gauges.energie;
    state.gauges.patience = data.gauges.patience;
    state.gauges.confiance = data.gauges.confiance;

    state.uptime_backend = data.uptime_backend;
    state.uptime_lyra = data.uptime_lyra;
    state.version = data.version;
    state.latency = data.latency;
    state.style = data.style;
  } catch (e) {
    console.error("Erreur fetchState Lyra:", e);
  }
}

async function updateGauge(gaugeKey, delta) {
  try {
    const res = await http.post("/lyra/update", {
      gauge: gaugeKey,
      delta
    });
    const data = res.data;

    state.gauges.chaleur = data.gauges.chaleur;
    state.gauges.energie = data.gauges.energie;
    state.gauges.patience = data.gauges.patience;
    state.gauges.confiance = data.gauges.confiance;

    state.uptime_lyra = data.uptime_lyra;

    await fetchState();

    const label = gaugeLabels[gaugeKey] || gaugeKey;
    const sign = delta > 0 ? "+" : "";
    addHistory(`${label} ${sign}${delta} (ajustement manuel)`);
  } catch (e) {
    addHistory(`Erreur lors de la mise à jour de ${gaugeLabels[gaugeKey] || gaugeKey}.`);
  }
}

function onSliderChange(gaugeKey, event) {
  const newValue = Number(event.target.value);
  const current = state.gauges[gaugeKey];
  const delta = newValue - current;
  if (delta !== 0) {
    updateGauge(gaugeKey, delta);
  }
}

async function resetLyra() {
  try {
    const res = await http.post("/lyra/update", {
      reset: true
    });
    const data = res.data;

    state.gauges.chaleur = data.gauges.chaleur;
    state.gauges.energie = data.gauges.energie;
    state.gauges.patience = data.gauges.patience;
    state.gauges.confiance = data.gauges.confiance;

    state.uptime_lyra = data.uptime_lyra;

    await fetchState();

    addHistory("Reset complet de Lyra.");
  } catch (e) {
    addHistory("Erreur lors du reset de Lyra.");
  }
}

function applyPreset(name) {
  const targets = {
    chaleureuse: { chaleur: 100, energie: 80, patience: 85, confiance: 75 },
    neutre: { chaleur: 60, energie: 60, patience: 60, confiance: 60 },
    froide: { chaleur: 20, energie: 30, patience: 40, confiance: 40 }
  };
  
  const target = targets[name];
  if (target) {
    Object.keys(target).forEach(key => {
      updateGauge(key, target[key] - state.gauges[key]);
    });
    addHistory(`Preset appliqué : ${name}.`);
  }
}

onMounted(() => {
  fetchState();
  setInterval(fetchState, 5000);
});
</script>

<template>
  <div class="flex h-full w-full overflow-hidden bg-slate-950 text-slate-200">
    <Sidebar />

    <div class="flex-1 flex flex-col relative min-w-0">
      <ChatHeader />

      <main class="flex-1 overflow-y-auto scrollbar-custom p-8">
        <div class="max-w-6xl mx-auto space-y-8 animate-slide-up">
          
          <!-- Page Header -->
          <div class="flex items-end justify-between border-b border-white/5 pb-6">
            <div>
              <h1 class="text-3xl font-bold font-outfit text-white mb-2">Centre de contrôle Lyra</h1>
              <p class="text-slate-500 text-sm">Ajustez la personnalité et les paramètres cognitifs de l'IA en temps réel.</p>
            </div>
          </div>

          <!-- Dashboard Grid -->
          <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
            
            <!-- Gauges & Controls -->
            <div class="lg:col-span-2 space-y-6">
              <section class="glass-card rounded-3xl p-8 space-y-8">
                <!-- Circular Gauges -->
                <div class="grid grid-cols-2 sm:grid-cols-4 gap-6">
                  <div v-for="(v, k) in gauges" :key="k" class="flex flex-col items-center gap-3">
                    <span class="text-[10px] uppercase font-bold tracking-widest text-slate-500">{{ gaugeLabels[k] }}</span>
                    <LyraGauge :value="v" :icon="k === 'chaleur' ? '🔥' : k === 'energie' ? '⚡' : k === 'patience' ? '🧘' : '⭐'" />
                  </div>
                </div>

                <!-- Sliders -->
                <div class="space-y-6 pt-4">
                  <div v-for="(v, k) in gauges" :key="k" class="flex items-center gap-4 group">
                    <div class="w-24 text-xs font-bold text-slate-400 group-hover:text-emerald-400 transition-colors">{{ gaugeLabels[k] }}</div>
                    <input
                      type="range"
                      min="0"
                      max="100"
                      class="flex-1 h-1.5 bg-white/5 rounded-full appearance-none cursor-pointer accent-emerald-500"
                      :value="v"
                      @input="onSliderChange(k, $event)"
                    />
                    <div class="w-10 text-right font-mono text-xs text-white">{{ v }}%</div>
                  </div>
                </div>

                <!-- Presets -->
                <div class="flex flex-wrap gap-3 pt-6 border-t border-white/5">
                  <button @click="applyPreset('chaleureuse')" class="btn-secondary text-[10px] uppercase tracking-widest bg-emerald-500/10 border-emerald-500/20 text-emerald-400 hover:bg-emerald-500/20">Chaleureuse</button>
                  <button @click="applyPreset('neutre')" class="btn-secondary text-[10px] uppercase tracking-widest">Neutre</button>
                  <button @click="applyPreset('froide')" class="btn-secondary text-[10px] uppercase tracking-widest bg-rose-500/10 border-rose-500/20 text-rose-400 hover:bg-rose-500/20">Concise</button>
                  <div class="flex-1"></div>
                  <button @click="resetLyra" class="px-4 py-2 text-[10px] uppercase font-bold tracking-widest rounded-lg bg-rose-600/10 text-rose-500 border border-rose-500/20 hover:bg-rose-600 hover:text-white transition-all">Reset</button>
                </div>
              </section>
            </div>

            <!-- Stats & History -->
            <div class="space-y-8">
              <LyraStylePreview :style="state.style" class="glass-card rounded-3xl p-6" />
              <LyraHistory :history="history" class="glass-card rounded-3xl p-6 h-[400px] overflow-hidden" />
            </div>

          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<style scoped>
/* Scoped specificities could go here, but shared classes are preferred */
</style>

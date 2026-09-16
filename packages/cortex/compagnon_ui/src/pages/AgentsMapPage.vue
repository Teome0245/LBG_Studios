<script setup>
import { onMounted, ref } from "vue";
import { http } from "@/api/http";
import Sidebar from "../components/Sidebar.vue";
import ChatHeader from "../components/ChatHeader.vue";

const loading = ref(true);
const error = ref(null);
const payload = ref(null);

async function load() {
  loading.value = true;
  error.value = null;
  try {
    const { data } = await http.get("/agents/map", { params: { _t: Date.now() } });
    payload.value = data;
  } catch (e) {
    const d = e?.response?.data;
    const detail =
      (typeof d?.detail === "string" && d.detail) ||
      (Array.isArray(d?.detail) && d.detail.map((x) => x?.msg || x).filter(Boolean).join("; ")) ||
      (typeof d === "string" && d) ||
      e?.message ||
      "Erreur réseau";
    error.value = e?.response?.status ? `${detail} (HTTP ${e.response.status})` : detail;
    payload.value = null;
  } finally {
    loading.value = false;
  }
}

onMounted(load);

function kindClass(kind) {
  if (kind === "internal") return "bg-slate-600/40 text-slate-200 border-slate-500/30";
  if (kind === "alias") return "bg-amber-500/15 text-amber-200 border-amber-500/25";
  if (kind === "capability") return "bg-violet-500/10 text-violet-300 border-violet-500/20";
  return "bg-emerald-500/10 text-emerald-300 border-emerald-500/20";
}
</script>

<template>
  <div class="flex h-full w-full overflow-hidden bg-slate-950 text-slate-200">
    <Sidebar />
    <div class="flex-1 flex flex-col relative min-w-0">
      <ChatHeader />
      <main class="flex-1 overflow-y-auto scrollbar-custom p-4 sm:p-6">
        <div class="max-w-5xl mx-auto space-y-6">
          <header class="flex flex-wrap items-end justify-between gap-4">
            <div>
              <h1 class="text-xl font-bold font-outfit text-white tracking-tight">
                Carte des agents
              </h1>
              <p class="text-sm text-slate-400 mt-1 max-w-xl">
                Rôles, variables d’environnement et URLs vues par l’orchestrateur. Les capabilities affichées sont celles
                déjà chargées en mémoire (rafraîchissement au démarrage / sync).
              </p>
            </div>
            <button
              type="button"
              class="px-3 py-2 rounded-lg text-sm font-medium bg-white/5 hover:bg-white/10 border border-white/10 transition-colors"
              :disabled="loading"
              @click="load"
            >
              Actualiser
            </button>
          </header>

          <p v-if="loading" class="text-slate-500 text-sm">Chargement…</p>
          <p v-else-if="error" class="text-red-400 text-sm">{{ error }}</p>

            <template v-else-if="payload">
            <section
              v-if="payload.cortex_team"
              class="rounded-xl border border-emerald-500/20 bg-emerald-950/20 p-4 backdrop-blur"
            >
              <h2 class="text-xs font-semibold uppercase tracking-widest text-emerald-400/80 mb-2">
                Team Cortex (sync live)
              </h2>
              <p class="text-sm text-slate-300">
                {{ payload.cortex_team.team_http_agents }} agents HTTP
                <span v-if="payload.cortex_team.pilot_synced">· pilot OK</span>
                <span v-else class="text-amber-400">· pilot indisponible</span>
                · {{ payload.cortex_team.orch_capability_count }} capabilities orchestrateur
              </p>
            </section>

            <section
              v-if="payload.capability_installer && payload.env_scope === 'dev'"
              class="rounded-xl border border-white/10 bg-slate-900/50 p-4 backdrop-blur"
            >
              <h2 class="text-xs font-semibold uppercase tracking-widest text-slate-400 mb-2">
                Auto-install capabilities
              </h2>
              <p class="text-sm text-slate-300 font-mono break-all">
                {{ payload.capability_installer.url }}
              </p>
              <p class="text-[11px] text-slate-500 mt-1">
                {{ payload.capability_installer.env_var }}
              </p>
            </section>

            <p v-if="payload.devops_routing?.mode === 'legacy'" class="text-xs text-slate-500">
              Cible DevOps active (lab DEV) :
              <span class="font-mono text-slate-300">{{ payload.devops_routing.target }}</span>
              (via DEVOPS_AGENT_TARGET)
            </p>
            <p v-else-if="payload.devops_routing?.mode === 'cortex_team'" class="text-xs text-slate-500">
              Routage DevOps / infra :
              <span class="font-mono text-emerald-400/90">{{ payload.devops_routing.label }}</span>
              <span class="text-slate-600">· legacy WSL/VM désactivé en prod CT100</span>
            </p>

            <div class="grid gap-4 sm:grid-cols-2">
              <article
                v-for="a in payload.agents"
                :key="a.id"
                class="rounded-xl border border-white/10 bg-slate-900/40 p-4 backdrop-blur flex flex-col gap-2"
              >
                <div class="flex items-start justify-between gap-2">
                  <div>
                    <h3 class="font-semibold text-white font-outfit">{{ a.label }}</h3>
                    <p class="text-xs font-mono text-slate-500">{{ a.id }}</p>
                  </div>
                  <span
                    class="text-[10px] uppercase tracking-wider px-2 py-0.5 rounded border shrink-0"
                    :class="kindClass(a.kind)"
                  >
                    {{ a.kind }}
                  </span>
                </div>
                <p class="text-sm text-slate-400 leading-snug">{{ a.description }}</p>
                <div v-if="a.env_var" class="text-[11px] text-slate-500">
                  <span class="text-slate-600">Env ·</span>
                  <span class="font-mono text-slate-400">{{ a.env_var }}</span>
                </div>
                <div v-if="a.base_url" class="text-xs font-mono text-emerald-400/90 break-all">
                  {{ a.base_url }}
                </div>
                <div v-else-if="a.kind !== 'internal'" class="text-xs text-slate-600 italic">URL non résolue</div>
                <div class="flex items-center gap-3 mt-auto pt-2 border-t border-white/5 text-[11px]">
                  <span
                    v-if="a.source === 'cortex_pilot'"
                    :class="a.team_status === 'ok' ? 'text-emerald-400' : 'text-amber-400'"
                  >
                    Team · {{ a.team_status || "?" }}
                  </span>
                  <span v-else-if="a.source === 'cortex_orch'" class="text-violet-400">Orchestrateur</span>
                  <span v-else :class="a.registered ? 'text-emerald-400' : 'text-red-400'">
                    {{ a.registered ? "Enregistré" : "Manquant du routeur" }}
                  </span>
                  <span class="text-slate-500">
                    {{ a.capability_count }} capability(ies)
                  </span>
                </div>
              </article>
            </div>
          </template>
        </div>
      </main>
    </div>
  </div>
</template>

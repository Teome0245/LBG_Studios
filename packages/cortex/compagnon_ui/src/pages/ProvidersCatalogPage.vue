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
    const { data } = await http.get("/providers/catalog", { params: { _t: Date.now() } });
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

function statusClass(status) {
  if (status === "up") return "text-emerald-400 bg-emerald-500/10 border-emerald-500/25";
  if (status === "down") return "text-red-400 bg-red-500/10 border-red-500/25";
  if (status === "unconfigured") return "text-slate-500 bg-slate-800/50 border-white/5";
  if (status === "alias") return "text-amber-300 bg-amber-500/10 border-amber-500/20";
  return "text-slate-400 bg-white/5 border-white/10";
}

function kindClass(kind) {
  if (kind === "local") return "bg-cyan-500/10 text-cyan-300 border-cyan-500/20";
  if (kind === "alias") return "bg-amber-500/10 text-amber-300 border-amber-500/20";
  return "bg-violet-500/10 text-violet-300 border-violet-500/20";
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
                Catalogue LLM
              </h1>
              <p class="text-sm text-slate-400 mt-1 max-w-xl">
                Providers locaux (Ollama .110 / .111) et distants — modèles, sondes, et audit
                dual Cortex (écarts + reco <span class="font-mono">ollama pull</span>).
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
            <section class="rounded-xl border border-white/10 bg-slate-900/40 p-4 backdrop-blur text-sm">
              <p class="text-slate-400">
                Scope <span class="font-mono text-slate-200">{{ payload.env_scope }}</span>
                · construit en <span class="font-mono">{{ payload.built_ms }} ms</span>
              </p>
              <p v-if="payload.routing?.fallback" class="text-slate-500 mt-2 text-xs">
                Fallback configuré :
                <span class="font-mono text-slate-300">
                  {{ payload.routing.fallback.provider }} / {{ payload.routing.fallback.name }}
                </span>
              </p>
              <p v-if="payload.routing?.effective_fallback" class="text-slate-500 mt-1 text-xs">
                Fallback effectif :
                <span class="font-mono text-emerald-400/90">
                  {{ payload.routing.effective_fallback.provider }} / {{ payload.routing.effective_fallback.name }}
                </span>
              </p>
            </section>

            <section
              v-if="payload.ollama_audit"
              class="rounded-xl border p-4 backdrop-blur"
              :class="
                payload.ollama_audit.ok
                  ? 'border-emerald-500/25 bg-emerald-950/20'
                  : 'border-amber-500/25 bg-amber-950/15'
              "
            >
              <div class="flex flex-wrap items-start justify-between gap-3 mb-3">
                <div>
                  <h2 class="text-xs font-semibold uppercase tracking-widest text-slate-400">
                    Audit Ollama dual (.110 / .111)
                  </h2>
                  <p class="text-sm text-slate-300 mt-1">
                    <span
                      class="font-mono text-xs px-1.5 py-0.5 rounded border"
                      :class="
                        payload.ollama_audit.ok
                          ? 'text-emerald-400 border-emerald-500/30'
                          : 'text-amber-300 border-amber-500/30'
                      "
                    >
                      {{ payload.ollama_audit.ok ? "ok" : "écarts" }}
                    </span>
                    · source
                    <span class="font-mono text-slate-400">{{ payload.ollama_audit.source }}</span>
                    · {{ payload.ollama_audit.model_count ?? 0 }} modèles
                  </p>
                </div>
              </div>

              <div class="grid gap-3 sm:grid-cols-2 text-xs mb-3">
                <div class="rounded-lg border border-white/5 bg-black/20 p-3">
                  <p class="text-slate-500 uppercase tracking-wider mb-1">Heavy</p>
                  <p class="font-mono text-slate-300 break-all">
                    {{ payload.ollama_audit.heavy?.base_url || payload.ollama_audit.base_url }}
                  </p>
                  <p class="text-slate-400 mt-1">
                    {{ (payload.ollama_audit.heavy?.names || []).join(", ") || "—" }}
                  </p>
                </div>
                <div class="rounded-lg border border-white/5 bg-black/20 p-3">
                  <p class="text-slate-500 uppercase tracking-wider mb-1">Light</p>
                  <p class="font-mono text-slate-300 break-all">
                    {{ payload.ollama_audit.light?.base_url || payload.ollama_audit.light_base_url }}
                  </p>
                  <p class="text-slate-400 mt-1">
                    {{ (payload.ollama_audit.light?.names || []).join(", ") || "—" }}
                  </p>
                </div>
              </div>

              <div v-if="payload.ollama_audit.gaps?.length" class="mb-3">
                <p class="text-[10px] uppercase tracking-widest text-amber-400/80 mb-1.5">
                  Écarts ({{ payload.ollama_audit.gaps.length }})
                </p>
                <ul class="text-xs text-amber-200/90 space-y-0.5 font-mono">
                  <li v-for="(g, i) in payload.ollama_audit.gaps" :key="i">{{ g }}</li>
                </ul>
              </div>

              <div v-if="payload.ollama_audit.pull_commands?.length" class="mb-3">
                <p class="text-[10px] uppercase tracking-widest text-cyan-400/80 mb-1.5">
                  Commandes ollama pull
                </p>
                <ul class="text-xs font-mono text-slate-300 space-y-1">
                  <li
                    v-for="(c, i) in payload.ollama_audit.pull_commands"
                    :key="i"
                    class="break-all"
                  >
                    {{ c.command }}
                  </li>
                </ul>
              </div>

              <div v-if="payload.ollama_audit.recommendations?.length">
                <p class="text-[10px] uppercase tracking-widest text-slate-500 mb-1.5">
                  Recommandations
                </p>
                <ul class="text-xs text-slate-400 space-y-1 list-disc list-inside">
                  <li v-for="(r, i) in payload.ollama_audit.recommendations" :key="i">
                    {{ r }}
                  </li>
                </ul>
              </div>
            </section>

            <div class="grid gap-4 sm:grid-cols-2">
              <article
                v-for="p in payload.providers"
                :key="p.id"
                class="rounded-xl border border-white/10 bg-slate-900/40 p-4 backdrop-blur flex flex-col gap-3"
              >
                <div class="flex items-start justify-between gap-2">
                  <div>
                    <h2 class="font-semibold text-white">{{ p.label }}</h2>
                    <p class="text-xs text-slate-500 font-mono mt-0.5">{{ p.id }}</p>
                  </div>
                  <span
                    class="text-[10px] uppercase tracking-widest font-bold px-2 py-1 rounded border shrink-0"
                    :class="statusClass(p.status)"
                  >
                    {{ p.status }}
                  </span>
                </div>

                <p class="text-sm text-slate-400">{{ p.description }}</p>

                <div class="flex flex-wrap gap-1.5">
                  <span
                    class="text-[10px] uppercase tracking-wider px-2 py-0.5 rounded border"
                    :class="kindClass(p.kind)"
                  >
                    {{ p.kind }}
                  </span>
                  <span
                    v-for="role in p.roles"
                    :key="role"
                    class="text-[10px] uppercase tracking-wider px-2 py-0.5 rounded border bg-white/5 text-slate-400 border-white/10"
                  >
                    {{ role }}
                  </span>
                </div>

                <p v-if="p.base_url" class="text-xs font-mono text-slate-500 break-all">
                  {{ p.base_url }}
                </p>
                <p v-if="p.alias_of" class="text-xs text-amber-400/80">
                  Alias → {{ p.alias_of }}
                </p>
                <p v-if="p.env_vars?.length" class="text-[11px] text-slate-500">
                  Env :
                  <span class="font-mono text-slate-400">{{ p.env_vars.join(", ") }}</span>
                  <span v-if="!p.configured" class="text-amber-400"> (non configuré)</span>
                </p>
                <p v-if="p.latency_ms != null" class="text-[11px] text-slate-500">
                  Latence sonde : <span class="font-mono">{{ Math.round(p.latency_ms) }} ms</span>
                </p>
                <p v-if="p.error" class="text-xs text-red-400/90 break-all">{{ p.error }}</p>

                <div v-if="p.models?.length" class="border-t border-white/5 pt-2">
                  <p class="text-[10px] uppercase tracking-widest text-slate-500 mb-1.5">
                    Modèles ({{ p.models_count }})
                  </p>
                  <ul class="text-xs font-mono text-slate-300 space-y-0.5 max-h-32 overflow-y-auto scrollbar-custom">
                    <li v-for="m in p.models" :key="m">{{ m }}</li>
                  </ul>
                </div>
                <p v-else-if="p.kind !== 'alias'" class="text-xs text-slate-600 italic">
                  Aucun modèle listé
                </p>
              </article>
            </div>

            <section
              v-if="payload.routing?.effective_tasks && Object.keys(payload.routing.effective_tasks).length"
              class="rounded-xl border border-white/10 bg-slate-900/30 p-4"
            >
              <h2 class="text-xs font-semibold uppercase tracking-widest text-slate-400 mb-3">
                Routing effectif (tasks)
              </h2>
              <div class="overflow-x-auto">
                <table class="w-full text-xs text-left">
                  <thead>
                    <tr class="text-slate-500 border-b border-white/5">
                      <th class="py-2 pr-4 font-medium">Tâche</th>
                      <th class="py-2 pr-4 font-medium">Effectif</th>
                      <th class="py-2 font-medium">Ignorés</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr
                      v-for="(entry, task) in payload.routing.effective_tasks"
                      :key="task"
                      class="border-b border-white/5 last:border-0"
                    >
                      <td class="py-2 pr-4 font-mono text-slate-300">{{ task }}</td>
                      <td class="py-2 pr-4 font-mono text-slate-400">
                        <span
                          v-for="(m, i) in entry.effective"
                          :key="`${m.provider}-${m.name}`"
                        >
                          <template v-if="i"> → </template>{{ m.provider }}/{{ m.name }}
                        </span>
                        <span v-if="!entry.effective?.length" class="text-slate-600 italic">—</span>
                      </td>
                      <td class="py-2 text-slate-500">{{ entry.skipped }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </section>
          </template>
        </div>
      </main>
    </div>
  </div>
</template>

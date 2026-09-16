<template>
  <div class="space-y-3">
    <div v-if="loading && !hasAny" class="text-slate-500 italic text-[10px]">
      Chargement roster…
    </div>
    <div v-else-if="!hasAny" class="text-slate-500 italic text-[10px]">
      Roster indisponible
    </div>

    <section v-for="sec in sections" :key="sec.key">
      <template v-if="sec.members.length">
        <h3 class="text-[11px] font-semibold uppercase opacity-60 tracking-widest mb-1.5">
          {{ sec.title }}
        </h3>
        <div class="space-y-1.5">
          <button
            v-for="a in sec.members"
            :key="a.id || a.name"
            type="button"
            class="w-full text-left rounded-lg border px-2.5 py-2 transition-colors hover:bg-white/5"
            :class="cardClass(a)"
            :title="`Mentionner ${mentionOf(a)}`"
            @click="onMention(a)"
          >
            <div class="flex items-start justify-between gap-2 mb-0.5">
              <strong class="text-[11px] text-slate-100 truncate">{{ a.name || a.id }}</strong>
              <span class="text-[10px] text-sky-300/90 shrink-0 font-mono">{{ mentionOf(a) }}</span>
            </div>
            <div v-if="a.role" class="text-[10px] text-slate-400 truncate">{{ a.role }}</div>
            <div v-if="a.function" class="text-[10px] text-slate-500 leading-snug mt-0.5">
              {{ a.function }}
            </div>
            <div v-if="a.host" class="text-[9px] text-slate-600 font-mono mt-0.5">{{ a.host }}</div>
          </button>
        </div>
      </template>
    </section>

    <p v-if="hasAny" class="text-[9px] text-slate-600 leading-snug">
      Clic → @mention dans le chat (Team + agents locaux)
    </p>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { http } from '@/api/http'
import { useChat } from '../composables/useChat'

const { appendMention } = useChat()

const loading = ref(false)
const roster = ref({ agents: [], team: [], humans: [], incarnations: [] })

const sections = computed(() => [
  { key: 'agents', title: 'Agents P03', members: roster.value.agents || [] },
  { key: 'team', title: 'Team studio', members: roster.value.team || [] },
  { key: 'humans', title: 'Humains', members: roster.value.humans || [] },
  { key: 'monde', title: 'Monde (en ligne)', members: roster.value.incarnations || [] },
])

const hasAny = computed(() =>
  sections.value.some((s) => (s.members || []).length > 0),
)

function mentionOf(a) {
  if (a?.mention) return a.mention
  const id = a?.id || a?.name || 'agent'
  return `@${String(id).replace(/^@/, '')}`
}

function cardClass(a) {
  const kind = a?.kind || 'agent'
  if (kind === 'incarnation') {
    return 'border-emerald-400/25 bg-emerald-400/5'
  }
  if (kind === 'team') {
    return 'border-violet-400/30 bg-violet-400/5'
  }
  if (kind === 'human') {
    return 'border-amber-400/35 bg-amber-400/5'
  }
  return 'border-sky-400/20 bg-sky-400/5'
}

function onMention(a) {
  // Humains : mention seule (pas de force Team). Agents / Team / Monde → Team Campus.
  appendMention(mentionOf(a))
}

async function load() {
  loading.value = true
  try {
    const res = await http.get('/monitor/cockpit', { params: { _t: Date.now() } })
    const r = res.data?.team_roster || {}
    roster.value = {
      agents: Array.isArray(r.agents) ? r.agents : [],
      team: Array.isArray(r.team) ? r.team : [],
      humans: Array.isArray(r.humans) ? r.humans : [],
      incarnations: Array.isArray(r.incarnations) ? r.incarnations : [],
    }
  } catch {
    /* keep last */
  } finally {
    loading.value = false
  }
}

let intervalId
onMounted(() => {
  load()
  intervalId = setInterval(load, 20000)
})
onUnmounted(() => {
  if (intervalId) clearInterval(intervalId)
})
</script>

<script setup>
import { nextTick, watch, ref, computed, onMounted } from 'vue'
import { useChat } from '../composables/useChat'
import ApprovalCard from './ApprovalCard.vue'
import ActionCard from './ActionCard.vue'
import ChatBreadcrumbs from './ChatBreadcrumbs.vue'
import ActivityEncart from './ActivityEncart.vue'

const { messages, loadHistory } = useChat()
const scrollRef = ref(null)
const viewFilter = ref('all')

onMounted(() => {
  loadHistory()
})

watch(messages, () => {
  nextTick(() => {
    if (scrollRef.value) {
      scrollRef.value.scrollTop = scrollRef.value.scrollHeight
    }
  })
}, { deep: true, immediate: true })

const crumbCounts = computed(() => {
  let moi = 0
  let ai = 0
  let timeline = 0
  for (const m of messages.value || []) {
    if (m.role === 'user') moi += 1
    else {
      ai += 1
      if (m.timeline?.length) timeline += 1
    }
  }
  return { moi, ai, timeline }
})

const visibleMessages = computed(() => {
  const list = messages.value || []
  const f = viewFilter.value
  if (f === 'moi') return list.filter((m) => m.role === 'user')
  if (f === 'ai') return list.filter((m) => m.role !== 'user')
  if (f === 'timeline') return list.filter((m) => m.role !== 'user' && m.timeline?.length)
  return list
})

function aiLabel(msg) {
  const src = (msg.source || '').toLowerCase()
  if (src === 'agir') return 'Compagnon · Agir'
  if (src === 'vision') return 'Compagnon · Vision'
  if (src === 'initiative') return 'Compagnon · Initiative'
  if (src.startsWith('team') || src.includes('campus')) return 'Team Ops'
  if (src.includes('cursor')) return 'Cursor Agent'
  if (src.includes('desktop')) return 'Agent Poste'
  if (src && src !== 'assistant' && src !== 'memory' && src !== 'user') return `AI · ${msg.source}`
  return 'Compagnon'
}

const parseContent = (content) => {
  if (!content) return []

  const parts = []
  const imageRegex = /!\[([^\]]*)\]\(([^)]+)\)/g
  let lastIndex = 0
  let match

  while ((match = imageRegex.exec(content)) !== null) {
    if (match.index > lastIndex) {
      parts.push({ type: 'text', value: content.slice(lastIndex, match.index) })
    }
    parts.push({ type: 'image', alt: match[1], url: match[2] })
    lastIndex = imageRegex.lastIndex
  }

  if (lastIndex < content.length) {
    parts.push({ type: 'text', value: content.slice(lastIndex) })
  }

  return parts.length > 0 ? parts : [{ type: 'text', value: content }]
}

function stepStatusClass(status) {
  if (status === 'ok') return 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10'
  if (status === 'error') return 'text-rose-400 border-rose-500/30 bg-rose-500/10'
  return 'text-slate-400 border-white/10 bg-white/5'
}

function displayContent(msg) {
  const c = msg.content || ''
  if (msg.followup?.steps?.length && c.includes('**Suite — recolle une ligne dans le chat :**')) {
    return c.split('---\n**Suite — recolle une ligne dans le chat :**')[0].trimEnd()
  }
  return c
}

function triggerCtrlK() {
  window.dispatchEvent(new KeyboardEvent('keydown', { key: 'k', ctrlKey: true, bubbles: true }))
}
</script>

<template>
  <div class="flex-1 overflow-y-auto scrollbar-custom p-4 sm:p-6" ref="scrollRef">
    <div class="max-w-4xl mx-auto space-y-6 pb-48">

      <ChatBreadcrumbs v-if="messages.length > 0" v-model="viewFilter" :counts="crumbCounts" />

      <!-- Empty state chaleureux : les 30 premières secondes sentent un compagnon -->
      <div v-if="messages.length === 0" class="flex flex-col items-center justify-center text-center py-12 sm:py-20 animate-slide-up">
        <div class="relative mb-5">
          <div class="h-20 w-20 rounded-3xl bg-gradient-to-tr from-emerald-500/20 via-teal-500/15 to-sky-500/10 border border-white/15 flex items-center justify-center shadow-2xl overflow-hidden ring-1 ring-white/10">
            <img src="/assets/icons/256/orchestrateur_happy.png" alt="Compagnon" class="w-16 h-16 object-contain" />
          </div>
          <span class="absolute -bottom-1 -right-1 h-5 w-5 rounded-full bg-slate-900 border-2 border-slate-950 flex items-center justify-center">
            <span class="h-2.5 w-2.5 rounded-full bg-emerald-400 animate-pulse-soft"></span>
          </span>
        </div>

        <h1 class="text-2xl sm:text-3xl font-extrabold font-outfit text-white tracking-tight mb-2">
          Compagnon Studio
        </h1>
        <p class="text-sm sm:text-base text-slate-300 max-w-lg mx-auto leading-relaxed mb-6">
          Présent pour dialoguer, concevoir et agir sur le poste sous ton contrôle (L2).
        </p>
        <p class="text-[11px] text-slate-500 font-mono">
          Écris ci-dessous · <button type="button" class="text-teal-400/90 hover:text-teal-300 underline-offset-2 hover:underline cursor-pointer" @click="triggerCtrlK">Ctrl+K</button> pour le pilotage · <span class="text-cyan-400/80">Agir</span> pour une action poste
        </p>
      </div>

      <div
        v-else-if="visibleMessages.length === 0"
        class="text-center py-12 text-slate-500 text-sm"
      >
        Aucun message pour ce filtre.
      </div>

      <!-- Fil de discussion -->
      <div
        v-for="(msg, index) in visibleMessages"
        :key="index"
        :class="[
          'flex animate-slide-up w-full gap-3.5 px-1',
          msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'
        ]"
      >
        <div class="h-9 w-9 rounded-2xl flex-shrink-0 flex items-center justify-center border border-white/15 overflow-hidden shadow-md bg-slate-900 ring-1 ring-white/10 mt-1">
          <img v-if="msg.role === 'user'" src="https://ui-avatars.com/api/?name=U&background=047857&color=fff" alt="User" class="w-full h-full object-cover" />
          <img v-else src="/assets/icons/256/orchestrateur_happy.png" alt="Compagnon" class="w-full h-full object-cover" />
        </div>

        <div
          :class="[
            'flex flex-col gap-1 max-w-[88%] sm:max-w-[82%]',
            msg.role === 'user' ? 'items-end' : 'items-start'
          ]"
        >
          <div
            :class="[
              'text-[14px] sm:text-[15px] leading-relaxed p-4 sm:p-5 rounded-2xl shadow-lg border backdrop-blur-md',
              msg.role === 'user'
                ? 'bg-emerald-950/40 border-emerald-500/30 text-slate-100 rounded-tr-none shadow-emerald-950/20'
                : 'glass-card text-slate-100 rounded-tl-none'
            ]"
          >
            <!-- Timeline (pliée/synthétique) -->
            <div
              v-if="msg.role === 'assistant' && msg.timeline?.length"
              class="mb-3.5 pb-3.5 border-b border-white/10"
              :class="viewFilter === 'timeline' ? 'ring-1 ring-cyan-500/20 rounded-xl p-2 -m-1' : ''"
            >
              <p class="text-[10px] uppercase tracking-widest font-bold text-slate-400 mb-2">
                Timeline
              </p>
              <ol class="space-y-1.5">
                <li
                  v-for="(step, si) in msg.timeline"
                  :key="si"
                  class="flex flex-wrap items-baseline gap-2 text-xs"
                >
                  <span
                    class="font-mono px-1.5 py-0.5 rounded border shrink-0 text-[10px]"
                    :class="stepStatusClass(step.status)"
                  >{{ step.kind }}</span>
                  <span class="text-slate-200 font-medium">{{ step.label }}</span>
                  <span v-if="step.detail" class="text-slate-500 break-all">{{ step.detail }}</span>
                  <span v-if="step.ms != null" class="text-slate-500 font-mono text-[10px]">{{ Math.round(step.ms) }}ms</span>
                </li>
              </ol>
            </div>

            <!-- Réflexion adoucie -->
            <div
              v-if="msg.role === 'assistant' && msg.reflection && viewFilter !== 'timeline'"
              class="mb-3 text-[11px] text-slate-400 flex flex-wrap gap-2 items-center bg-white/5 px-2.5 py-1.5 rounded-lg border border-white/5"
            >
              <span class="uppercase tracking-widest font-bold text-cyan-400 text-[9px]">Réflexion</span>
              <span class="font-mono text-slate-300">{{ msg.reflection.action }}</span>
              <span class="text-slate-600">·</span>
              <span class="text-slate-300">{{ msg.reflection.reason }}</span>
              <span v-if="msg.reflection.source" class="font-mono text-slate-500 text-[10px]">({{ msg.reflection.source }})</span>
            </div>

            <!-- Cursor Agent info -->
            <div
              v-if="msg.role === 'assistant' && msg.cursor?.agent_url && viewFilter !== 'timeline'"
              class="mb-3 text-xs rounded-xl border border-violet-500/30 bg-violet-500/10 px-3 py-2"
            >
              <div class="flex items-center gap-1.5 text-violet-300 font-semibold">
                <span>Cursor Agent</span>
                <span class="text-slate-500">·</span>
                <span class="font-mono text-slate-400 text-xs">{{ msg.cursor.status || 'actif' }}</span>
              </div>
              <a
                :href="msg.cursor.agent_url"
                target="_blank"
                rel="noopener noreferrer"
                class="block mt-1 text-violet-300 hover:text-violet-200 underline underline-offset-2 break-all text-xs"
              >{{ msg.cursor.agent_url }}</a>
            </div>

            <!-- Contenu textuel et multimédia -->
            <div v-if="viewFilter !== 'timeline'" class="space-y-3">
              <div v-if="msg.images?.length" class="flex flex-wrap gap-2 mb-1" :class="msg.role === 'user' ? 'justify-end' : 'justify-start'">
                <img
                  v-for="(src, ii) in msg.images"
                  :key="ii"
                  :src="src.startsWith('data:') ? src : `data:image/jpeg;base64,${src}`"
                  alt="Pièce jointe"
                  class="max-h-40 max-w-[220px] rounded-xl border border-white/15 object-cover shadow-md"
                />
              </div>
              <template v-for="(part, pIndex) in parseContent(displayContent(msg))" :key="pIndex">
                <div v-if="part.type === 'text'" class="whitespace-pre-wrap leading-relaxed">{{ part.value }}</div>
                <div v-else-if="part.type === 'image'" class="my-2">
                  <img :src="part.url" :alt="part.alt" class="max-w-full rounded-xl border border-white/10 shadow-lg hover:scale-[1.01] transition-transform cursor-zoom-in" />
                </div>
              </template>
            </div>

            <ApprovalCard
              v-if="msg.role === 'assistant' && msg.approval?.tasks?.length && viewFilter !== 'timeline'"
              :approval="msg.approval"
            />

            <ActionCard
              v-if="msg.role === 'assistant' && msg.actionProposal && viewFilter !== 'timeline'"
              :proposal="msg.actionProposal"
              :source-text="msg.actionSourceText || ''"
            />

            <!-- Pied de message : modèle et latence discrets -->
            <div
              v-if="msg.role === 'assistant' && viewFilter !== 'timeline' && (msg.model || msg.latency || msg.provider)"
              class="mt-3.5 pt-2.5 border-t border-white/10 flex flex-wrap items-center gap-2 text-[10px]"
            >
              <div v-if="msg.model" class="flex items-center gap-1.5 px-2 py-0.5 rounded-md bg-white/5 border border-white/10 text-slate-300 font-mono">
                <span class="uppercase font-bold text-emerald-400">Modèle</span>
                <span>{{ msg.model }}</span>
              </div>
              <div v-if="msg.provider" class="text-slate-400 uppercase font-semibold">
                {{ msg.provider }}
              </div>
              <div v-if="msg.latency" class="text-slate-500 font-mono">
                {{ Number(msg.latency).toFixed(2) }}s
              </div>
            </div>
          </div>

          <span class="text-[10px] text-slate-400 font-bold tracking-wider uppercase px-2 mt-0.5">
            {{ msg.role === 'user' ? 'Vous' : aiLabel(msg) }}
          </span>
        </div>
      </div>

      <div class="px-1">
        <ActivityEncart />
      </div>
    </div>
  </div>
</template>

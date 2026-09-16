<script setup>
import { nextTick, watch, ref, computed, onMounted } from 'vue'
import { useChat } from '../composables/useChat'
import ApprovalCard from './ApprovalCard.vue'
import ActionCard from './ActionCard.vue'
import FollowupChips from './FollowupChips.vue'
import ChatBreadcrumbs from './ChatBreadcrumbs.vue'

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
  if (src === 'agir') return 'AI · Agir'
  if (src === 'initiative') return 'AI · Initiative'
  if (src.startsWith('team') || src.includes('campus')) return 'AI · Team'
  if (src.includes('cursor')) return 'AI · Cursor'
  if (src.includes('desktop')) return 'AI · Desktop'
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
  if (status === 'error') return 'text-red-400 border-red-500/30 bg-red-500/10'
  return 'text-slate-400 border-white/10 bg-white/5'
}

function displayContent(msg) {
  const c = msg.content || ''
  if (msg.followup?.steps?.length && c.includes('**Suite — recolle une ligne dans le chat :**')) {
    return c.split('---\n**Suite — recolle une ligne dans le chat :**')[0].trimEnd()
  }
  return c
}
</script>

<template>
  <div class="flex-1 overflow-y-auto scrollbar-custom p-6" ref="scrollRef">
    <div class="max-w-4xl mx-auto space-y-10 pb-40">

      <ChatBreadcrumbs v-model="viewFilter" :counts="crumbCounts" />

      <div v-if="messages.length === 0" class="h-full flex flex-col items-center justify-center text-center py-20 opacity-50 font-outfit">
        <div class="h-20 w-20 rounded-3xl bg-white/5 border border-white/10 flex items-center justify-center mb-6 shadow-2xl">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
          </svg>
        </div>
        <h2 class="text-2xl font-bold text-white mb-2">Compagnon</h2>
        <p class="text-sm max-w-md mx-auto">
          Présent pour dialoguer, concevoir et agir sous ton contrôle.
          Team, Jobs et Desktop restent dans Pilot quand tu veux le cockpit ops.
        </p>
      </div>

      <div
        v-else-if="visibleMessages.length === 0"
        class="text-center py-12 text-slate-500 text-sm"
      >
        Aucun message pour ce filtre.
      </div>

      <div
        v-for="(msg, index) in visibleMessages"
        :key="index"
        :class="[
          'flex animate-slide-up w-full gap-4 px-2',
          msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'
        ]"
      >
        <div class="h-10 w-10 rounded-xl flex-shrink-0 flex items-center justify-center border border-white/20 font-bold overflow-hidden shadow-lg bg-slate-900 ring-1 ring-white/10">
          <img v-if="msg.role === 'user'" src="https://ui-avatars.com/api/?name=U&background=10b981&color=fff" alt="User" />
          <img v-else src="/assets/icons/256/orchestrateur_happy.png" alt="AI" class="w-full h-full object-cover" />
        </div>

        <div
          :class="[
            'flex flex-col gap-1.5 max-w-[85%] sm:max-w-[80%]',
            msg.role === 'user' ? 'items-end' : 'items-start'
          ]"
        >
          <div
            :class="[
              'text-base md:text-lg leading-relaxed p-5 rounded-3xl shadow-xl border backdrop-blur-md',
              msg.role === 'user'
                ? 'bg-emerald-500/20 border-emerald-500/40 text-slate-50 rounded-tr-none'
                : 'bg-white/10 border-white/20 text-slate-50 rounded-tl-none'
            ]"
          >
            <div
              v-if="msg.role === 'assistant' && msg.timeline?.length"
              class="mb-4 pb-4 border-b border-white/10"
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
                    class="font-mono px-1.5 py-0.5 rounded border shrink-0"
                    :class="stepStatusClass(step.status)"
                  >{{ step.kind }}</span>
                  <span class="text-slate-200 font-medium">{{ step.label }}</span>
                  <span v-if="step.detail" class="text-slate-500 break-all">{{ step.detail }}</span>
                  <span v-if="step.ms != null" class="text-slate-600 font-mono">{{ Math.round(step.ms) }}ms</span>
                </li>
              </ol>
            </div>

            <div
              v-if="msg.role === 'assistant' && msg.reflection && viewFilter !== 'timeline'"
              class="mb-3 text-[11px] text-slate-400 flex flex-wrap gap-2 items-center"
            >
              <span class="uppercase tracking-widest font-bold text-cyan-400/90">Réflexion</span>
              <span class="font-mono text-slate-300">{{ msg.reflection.action }}</span>
              <span class="text-slate-600">·</span>
              <span>{{ msg.reflection.reason }}</span>
              <span v-if="msg.reflection.source" class="font-mono text-slate-500">({{ msg.reflection.source }})</span>
            </div>

            <div
              v-if="msg.role === 'assistant' && msg.cursor?.agent_url && viewFilter !== 'timeline'"
              class="mb-3 text-xs rounded-lg border border-violet-500/25 bg-violet-500/10 px-3 py-2"
            >
              <span class="text-violet-300 font-semibold">Cursor Agent</span>
              <span class="text-slate-500 mx-1.5">·</span>
              <span class="font-mono text-slate-400">{{ msg.cursor.status || '…' }}</span>
              <a
                :href="msg.cursor.agent_url"
                target="_blank"
                rel="noopener noreferrer"
                class="block mt-1 text-violet-300 hover:text-violet-200 underline underline-offset-2 break-all"
              >{{ msg.cursor.agent_url }}</a>
            </div>

            <div v-if="viewFilter !== 'timeline'" class="space-y-4">
              <template v-for="(part, pIndex) in parseContent(displayContent(msg))" :key="pIndex">
                <div v-if="part.type === 'text'" class="whitespace-pre-wrap">{{ part.value }}</div>
                <div v-else-if="part.type === 'image'" class="my-2">
                  <img :src="part.url" :alt="part.alt" class="max-w-full rounded-xl border border-white/10 shadow-lg hover:scale-[1.02] transition-transform cursor-zoom-in" />
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

            <FollowupChips
              v-if="msg.role === 'assistant' && msg.followup?.steps?.length && viewFilter !== 'timeline'"
              :followup="msg.followup"
            />

            <div
              v-if="msg.role === 'assistant' && viewFilter !== 'timeline' && (msg.model || msg.latency || msg.provider)"
              class="mt-5 pt-4 border-t border-white/10 flex flex-wrap items-center gap-3"
            >
              <div v-if="msg.model" class="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-white/10 border border-white/10">
                <span class="text-[10px] uppercase font-black text-emerald-400 tracking-widest">Model</span>
                <span class="text-xs font-bold text-slate-100">{{ msg.model }}</span>
              </div>
              <div v-if="msg.provider" class="text-[10px] uppercase font-bold text-slate-500 tracking-widest">
                {{ msg.provider }}
              </div>
              <div v-if="msg.latency" class="text-xs text-slate-400 font-mono font-bold">
                {{ Number(msg.latency).toFixed(2) }}s
              </div>
            </div>
          </div>

          <span class="text-[11px] text-slate-300 font-black tracking-widest uppercase mt-1 px-2">
            {{ msg.role === 'user' ? 'Utilisateur' : aiLabel(msg) }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

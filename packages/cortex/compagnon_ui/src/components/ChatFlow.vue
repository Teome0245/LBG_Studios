<script setup>
import { nextTick, watch, ref, computed, onMounted } from 'vue'
import { useChat } from '../composables/useChat'
import ApprovalCard from './ApprovalCard.vue'
import ActionCard from './ActionCard.vue'
import ContextJournal from './ContextJournal.vue'
import ChatBreadcrumbs from './ChatBreadcrumbs.vue'
import ActivityEncart from './ActivityEncart.vue'
import { getStudioGoal } from '@/lib/studioGoal'
import {
  mandateAskIntents,
  mandateAskMessage,
  mandateNeedsAsk,
  setMandate,
} from '@/lib/mandate'
import { recipesForEmptyState, dispatchRecipeAsk } from '@/lib/recipes'
import { proposeAction } from '@/lib/agir'
import { jobContractToPilotContext, formatJobBrief } from '@/lib/jobContract'
import {
  startActivity,
  activityLog,
  endActivity,
} from '@/composables/useActivity'

import {
  WORLD_NOTIF_CATEGORIES,
  loadWorldNotifPrefs,
  saveWorldNotifPrefs,
  syncWorldNotifPrefs,
} from '@/lib/worldNotifPrefs'
import { resolveRouteTier, routeTierLabel } from '@/lib/modelRoute'

const { messages, loadHistory, addUserMessage, addMessage, breatheConversation, startNewChat } =
  useChat()
const scrollRef = ref(null)
const viewFilter = ref('all')
const studioGoalTitle = computed(() => getStudioGoal().goal?.title || 'Veiller Jobs L2')
const showMandateAsk = ref(false)
const mandateChips = mandateAskIntents()
const recipeChips = recipesForEmptyState(7)
const recipeBusy = ref('')
const worldPrefs = ref(loadWorldNotifPrefs())

onMounted(() => {
  loadHistory()
  showMandateAsk.value = mandateNeedsAsk()
  void syncWorldNotifPrefs(worldPrefs.value)
})

function toggleWorldPref(id) {
  const next = { ...worldPrefs.value, [id]: !worldPrefs.value[id] }
  worldPrefs.value = saveWorldNotifPrefs(next)
  void syncWorldNotifPrefs(worldPrefs.value)
}

function onBreathe() {
  breatheConversation()
}

function onNewThread() {
  startNewChat()
}

watch(messages, () => {
  nextTick(() => {
    if (scrollRef.value) {
      scrollRef.value.scrollTop = scrollRef.value.scrollHeight
    }
  })
}, { deep: true, immediate: true })

function pickMandate(intent) {
  if (!intent?.mandateScope) return
  setMandate([intent.mandateScope])
  showMandateAsk.value = false
  const goal = getStudioGoal()
  addUserMessage(`Mandat · ${intent.label}`)
  addMessage({
    role: 'assistant',
    content:
      `OK — je veille prioritairement « ${intent.label} » pour ~4 h` +
      ` (objectif · ${goal?.goal?.title || intent.label}).` +
      `\nJe proposerai des actions dans ce périmètre ; Garde infra reste prioritaire.`,
    source: 'mandate',
    state: 'orchestrateur-happy',
  })
}

async function pickRecipe(recipe) {
  if (!recipe || recipeBusy.value) return
  if (recipe.kind === 'ask' && recipe.prompt) {
    dispatchRecipeAsk(recipe)
    return
  }
  if (recipe.kind !== 'agir' || !recipe.sourceText) return
  recipeBusy.value = recipe.id
  startActivity(`Recette · ${recipe.label}`, ['agir', 'recipe'])
  activityLog(recipe.sourceText.slice(0, 120))
  addUserMessage(`Recette · ${recipe.label}`)
  try {
    const ctx = jobContractToPilotContext(recipe.contract)
    const { proposal, reason } = await proposeAction(recipe.sourceText, ctx)
    if (!proposal) {
      activityLog(reason || 'aucune action', 'warn')
      endActivity('error')
      addMessage({
        role: 'assistant',
        content: reason || 'Aucune action sûre reconnue pour cette recette.',
        source: 'agir',
      })
      return
    }
    activityLog(`${proposal.capability || 'ok'}`, 'ok')
    endActivity('done', 'Carte prête — Dry-run / Réel')
    const brief = formatJobBrief(recipe.contract)
    addMessage({
      role: 'assistant',
      content: `${proposal.summary || recipe.label}\n\n${brief}`,
      source: 'agir',
      actionProposal: proposal,
      actionSourceText: recipe.sourceText,
      jobContract: recipe.contract,
    })
  } catch (e) {
    endActivity('error', String(e?.message || e))
    addMessage({
      role: 'assistant',
      content: `Recette impossible : ${e?.message || e}`,
      source: 'error',
    })
  } finally {
    recipeBusy.value = ''
  }
}
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

/** Évite la bulle grise vide (SSE terminé sans texte). */
function msgHasBubbleBody(msg) {
  if (msg.role === 'user') return true
  if (msg.streamThinking || msg.streaming) return true
  if (String(msg.content || '').trim()) return true
  if (msg.timeline?.length || msg.reflection || msg.actionProposal) return true
  if (msg.approval?.tasks?.length || msg.cursor?.agent_url || msg.images?.length) return true
  if (msg.model || msg.latency || msg.provider) return true
  if (msg.context_journal) return true
  return false
}

/** Journal A1 : fusion job_contract client si présent sur la bulle Agir. */
function journalForMessage(msg) {
  const base = msg.context_journal
  const contract = msg.jobContract
  if (!contract?.objective) return base || null
  const block = {
    id: 'job_contract',
    label: 'Job contract',
    summary: String(contract.objective).slice(0, 120),
    chars: 0,
  }
  const blocks = Array.isArray(base?.blocks) ? [...base.blocks] : []
  if (!blocks.some((b) => b?.id === 'job_contract')) {
    blocks.push(block)
  }
  const total = blocks.reduce((n, b) => n + (Number(b?.chars) || 0), 0)
  return {
    ...(base && typeof base === 'object' ? base : {}),
    blocks,
    count: blocks.length,
    empty: blocks.length === 0,
    total_chars: total,
  }
}

function isOpsChromeMessage(msg) {
  /** Agir / Team / Cursor = chrome ops utile ; ask/réponse/causerie = replié. */
  const action = String(msg?.reflection?.action || '').toLowerCase()
  if (action === 'answer') return false
  const src = String(msg?.source || '').toLowerCase()
  if (src === 'agir' || src.startsWith('team') || src.includes('campus')) return true
  if (src.includes('cursor') || src.includes('desktop') || src === 'vision') return true
  if (msg?.actionProposal || msg?.approval?.tasks?.length) return true
  return false
}

function timelineOpenByDefault(msg) {
  return viewFilter.value === 'timeline' || isOpsChromeMessage(msg)
}

function triggerCtrlK() {
  window.dispatchEvent(new KeyboardEvent('keydown', { key: 'k', ctrlKey: true, bubbles: true }))
}
</script>

<template>
  <div class="flex-1 overflow-y-auto scrollbar-custom p-4 sm:p-6" ref="scrollRef">
    <div class="max-w-4xl mx-auto space-y-6 pb-48">

      <ChatBreadcrumbs v-if="messages.length > 0" v-model="viewFilter" :counts="crumbCounts" />

      <!-- A2 — Respire / Nouveau fil aussi hors empty state (fil saturé) -->
      <div
        v-if="messages.length > 0"
        class="flex flex-wrap gap-2 justify-end px-1 -mt-2 mb-1"
      >
        <button
          type="button"
          class="rounded-lg border border-white/10 bg-slate-950/40 px-2.5 py-1 text-[10px] text-slate-400 hover:border-cyan-400/40 hover:text-cyan-100 transition-colors"
          title="Compacte le fil, garde mandat"
          @click="onBreathe"
        >
          Respire
        </button>
        <button
          type="button"
          class="rounded-lg border border-white/10 bg-slate-950/40 px-2.5 py-1 text-[10px] text-slate-400 hover:border-cyan-400/40 hover:text-cyan-100 transition-colors"
          title="Nouvelle conversation"
          @click="onNewThread"
        >
          Nouveau fil
        </button>
      </div>

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

        <div
          v-if="showMandateAsk"
          class="w-full max-w-md mx-auto mb-6 rounded-2xl border border-teal-500/25 bg-teal-500/10 px-4 py-3.5 text-left"
        >
          <p class="text-[10px] uppercase tracking-wider text-teal-300/80 font-semibold mb-1.5">Priorité · mandat</p>
          <p class="text-sm text-slate-200 leading-snug mb-3">{{ mandateAskMessage() }}</p>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="chip in mandateChips"
              :key="chip.id"
              type="button"
              class="rounded-xl border border-teal-400/35 bg-slate-950/50 px-3 py-1.5 text-xs font-medium text-teal-100 hover:bg-teal-500/20 hover:border-teal-300/50 transition-colors"
              :title="chip.hint"
              @click="pickMandate(chip)"
            >
              {{ chip.label }}
            </button>
          </div>
        </div>

        <div class="w-full max-w-lg mx-auto mb-6 text-left">
          <p class="text-[10px] uppercase tracking-wider text-slate-400 font-semibold mb-2 px-1">
            Recettes · job clair
          </p>
          <div class="flex flex-wrap gap-2 justify-center">
            <button
              v-for="r in recipeChips"
              :key="r.id"
              type="button"
              class="rounded-xl border border-white/15 bg-slate-950/40 px-3 py-1.5 text-xs font-medium text-slate-200 hover:bg-teal-500/15 hover:border-teal-400/40 hover:text-teal-100 transition-colors disabled:opacity-50"
              :title="`${r.hint} · ${r.contract.objective}`"
              :disabled="!!recipeBusy"
              @click="pickRecipe(r)"
            >
              {{ recipeBusy === r.id ? '…' : r.label }}
            </button>
          </div>
        </div>

        <div class="w-full max-w-md mx-auto mb-5 text-left">
          <p class="text-[10px] uppercase tracking-wider text-slate-400 font-semibold mb-2 px-1 text-center">
            Rapports monde
          </p>
          <div class="flex flex-wrap gap-2 justify-center">
            <button
              v-for="c in WORLD_NOTIF_CATEGORIES"
              :key="c.id"
              type="button"
              class="rounded-xl border px-3 py-1.5 text-xs font-medium transition-colors"
              :class="worldPrefs[c.id]
                ? 'border-teal-400/40 bg-teal-500/15 text-teal-100'
                : 'border-white/10 bg-slate-950/30 text-slate-500'"
              :title="c.hint"
              @click="toggleWorldPref(c.id)"
            >
              {{ c.label }}
            </button>
          </div>
        </div>

        <div class="flex flex-wrap gap-2 justify-center mb-4">
          <button
            type="button"
            class="rounded-xl border border-white/15 bg-slate-950/40 px-3 py-1.5 text-xs text-slate-300 hover:border-cyan-400/40 hover:text-cyan-100 transition-colors"
            title="Compacte le fil, garde mandat"
            @click="onBreathe"
          >
            Respire
          </button>
          <button
            type="button"
            class="rounded-xl border border-white/15 bg-slate-950/40 px-3 py-1.5 text-xs text-slate-300 hover:border-cyan-400/40 hover:text-cyan-100 transition-colors"
            title="Nouvelle conversation"
            @click="onNewThread"
          >
            Nouveau fil
          </button>
        </div>

        <p class="text-[11px] text-slate-500 font-mono">
          Écris ci-dessous · <button type="button" class="text-teal-400/90 hover:text-teal-300 underline-offset-2 hover:underline cursor-pointer" @click="triggerCtrlK">Ctrl+K</button> pour le pilotage · <span class="text-cyan-400/80">Agir</span> pour une action poste
        </p>
        <p class="mt-3 text-[11px] text-teal-400/70">
          Objectif actif · {{ studioGoalTitle }}
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
            v-if="msgHasBubbleBody(msg)"
            :class="[
              'text-[14px] sm:text-[15px] leading-relaxed p-4 sm:p-5 rounded-2xl shadow-lg border backdrop-blur-md',
              msg.role === 'user'
                ? 'bg-emerald-950/40 border-emerald-500/30 text-slate-100 rounded-tr-none shadow-emerald-950/20'
                : 'glass-card text-slate-100 rounded-tl-none'
            ]"
          >
            <!-- A1 — Contexte injecté ce tour (replié) -->
            <ContextJournal
              v-if="msg.role === 'assistant' && journalForMessage(msg) && viewFilter !== 'timeline'"
              :journal="journalForMessage(msg)"
              :open-by-default="isOpsChromeMessage(msg)"
            />

            <!-- Timeline — D6.3 : repliée par défaut en mode ask/réponse -->
            <details
              v-if="msg.role === 'assistant' && msg.timeline?.length"
              class="mb-3.5 pb-3.5 border-b border-white/10 group/tl"
              :class="viewFilter === 'timeline' ? 'ring-1 ring-cyan-500/20 rounded-xl p-2 -m-1' : ''"
              :open="timelineOpenByDefault(msg) ? true : undefined"
            >
              <summary
                class="text-[10px] uppercase tracking-widest font-bold text-slate-400 mb-0 cursor-pointer select-none list-none inline-flex items-center gap-1.5 hover:text-slate-300 [&::-webkit-details-marker]:hidden"
              >
                <span class="opacity-70 group-open/tl:rotate-90 transition-transform inline-block">›</span>
                Timeline
                <span class="font-mono text-[9px] opacity-60 normal-case tracking-normal">{{ msg.timeline.length }}</span>
              </summary>
              <ol class="space-y-1.5 mt-2">
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
            </details>

            <!-- Réflexion — D6.3 : repliée sauf Agir/ops -->
            <details
              v-if="msg.role === 'assistant' && msg.reflection && viewFilter !== 'timeline'"
              class="mb-3 text-[11px] text-slate-400 group/rf"
              :open="isOpsChromeMessage(msg) ? true : undefined"
            >
              <summary
                class="flex flex-wrap gap-2 items-center bg-white/5 px-2.5 py-1.5 rounded-lg border border-white/5 cursor-pointer select-none list-none [&::-webkit-details-marker]:hidden hover:bg-white/[0.07]"
              >
                <span class="uppercase tracking-widest font-bold text-cyan-400 text-[9px]">Réflexion</span>
                <span class="font-mono text-slate-300 truncate max-w-[12rem]">{{ msg.reflection.action }}</span>
                <span class="text-slate-600 opacity-60 group-open/rf:hidden">· détail</span>
              </summary>
              <div class="mt-1.5 px-2.5 text-slate-300">
                <span>{{ msg.reflection.reason }}</span>
                <span v-if="msg.reflection.source" class="font-mono text-slate-500 text-[10px] ml-1">({{ msg.reflection.source }})</span>
              </div>
            </details>

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

            <!-- Contenu textuel et multimédia (+ indicateur SSE 1.2) -->
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
              <div
                v-if="msg.streamThinking && !msg.content"
                class="flex items-center gap-2 text-xs text-slate-400"
                aria-live="polite"
              >
                <span class="inline-flex gap-1" aria-hidden="true">
                  <span class="h-1.5 w-1.5 rounded-full bg-teal-400/80 animate-pulse" />
                  <span class="h-1.5 w-1.5 rounded-full bg-teal-400/60 animate-pulse [animation-delay:150ms]" />
                  <span class="h-1.5 w-1.5 rounded-full bg-teal-400/40 animate-pulse [animation-delay:300ms]" />
                </span>
                <span>Réflexion…</span>
              </div>
              <template v-for="(part, pIndex) in parseContent(displayContent(msg))" :key="pIndex">
                <div v-if="part.type === 'text'" class="whitespace-pre-wrap leading-relaxed">{{ part.value }}</div>
                <div v-else-if="part.type === 'image'" class="my-2">
                  <img :src="part.url" :alt="part.alt" class="max-w-full rounded-xl border border-white/10 shadow-lg hover:scale-[1.01] transition-transform cursor-zoom-in" />
                </div>
              </template>
              <span
                v-if="msg.streaming && msg.content"
                class="inline-block w-1.5 h-4 align-text-bottom bg-teal-400/70 animate-pulse"
                aria-hidden="true"
              />
            </div>

            <ApprovalCard
              v-if="msg.role === 'assistant' && msg.approval?.tasks?.length && viewFilter !== 'timeline'"
              :approval="msg.approval"
            />

            <ActionCard
              v-if="msg.role === 'assistant' && msg.actionProposal && viewFilter !== 'timeline'"
              :proposal="msg.actionProposal"
              :source-text="msg.actionSourceText || ''"
              :job-contract="msg.jobContract || null"
            />

            <!-- Pied modèle/latence — D6.3 : discret / replié en ask -->
            <details
              v-if="msg.role === 'assistant' && viewFilter !== 'timeline' && (msg.model || msg.latency || msg.provider)"
              class="mt-3.5 pt-2.5 border-t border-white/10 group/meta"
              :open="isOpsChromeMessage(msg) ? true : undefined"
            >
              <summary
                class="text-[10px] text-slate-500 cursor-pointer select-none list-none inline-flex items-center gap-1.5 hover:text-slate-300 [&::-webkit-details-marker]:hidden"
              >
                <span class="opacity-70 group-open/meta:rotate-90 transition-transform inline-block">›</span>
                Méta
                <span v-if="msg.model && !isOpsChromeMessage(msg)" class="font-mono text-slate-400 truncate max-w-[10rem]">{{ msg.model }}</span>
              </summary>
              <div class="mt-2 flex flex-wrap items-center gap-2 text-[10px]">
                <div v-if="msg.model" class="flex items-center gap-1.5 px-2 py-0.5 rounded-md bg-white/5 border border-white/10 text-slate-300 font-mono">
                  <span class="uppercase font-bold text-emerald-400">Modèle</span>
                  <span>{{ msg.model }}</span>
                </div>
                <div
                  v-if="routeTierLabel(msg)"
                  class="px-2 py-0.5 rounded-md border font-semibold uppercase tracking-wide"
                  :class="resolveRouteTier(msg) === 'heavy'
                    ? 'border-amber-500/30 bg-amber-500/10 text-amber-200'
                    : 'border-sky-500/30 bg-sky-500/10 text-sky-200'"
                >
                  {{ routeTierLabel(msg) }}
                </div>
                <div v-if="msg.provider" class="text-slate-400 uppercase font-semibold">
                  {{ msg.provider }}
                </div>
                <div v-if="msg.latency" class="text-slate-500 font-mono">
                  {{ Number(msg.latency).toFixed(2) }}s
                </div>
              </div>
            </details>
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

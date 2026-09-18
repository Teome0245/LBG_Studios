<script setup>
import { computed, ref } from 'vue'
import { useActivity } from '@/composables/useActivity'
import { PILOTAGE_BAR } from '@/lib/pilotageActions'
import { proposeAction } from '@/lib/agir'
import { useChat } from '@/composables/useChat'

const { current, toggleActivityOpen, clearActivity } = useActivity()
const { addUserMessage, addMessage, queuePrompt } = useChat()
const nextBusy = ref('')

const quickNext = computed(() => {
  if (!current.value) return []
  if (current.value.phase !== 'done' && current.value.phase !== 'error') return []
  const tools = (current.value.tools || []).join(' ')
  if (tools.includes('desktop') || tools.includes('agir')) {
    return PILOTAGE_BAR.filter((a) =>
      ['probe_ad', 'open_jobs', 'open_desktop', 'team_status'].includes(a.id)
    ).slice(0, 3)
  }
  return PILOTAGE_BAR.filter((a) =>
    ['probe_lan', 'team_status', 'open_jobs'].includes(a.id)
  ).slice(0, 3)
})

function lineClass(level) {
  if (level === 'ok') return 'text-emerald-400'
  if (level === 'warn') return 'text-amber-300'
  if (level === 'err') return 'text-rose-400'
  return 'text-slate-400'
}

async function runQuick(a) {
  if (!a || nextBusy.value) return
  if (a.kind === 'link' && a.href) {
    window.open(a.href, '_blank', 'noopener,noreferrer')
    return
  }
  if (a.kind === 'ask' && a.prompt) {
    queuePrompt(a.prompt)
    try {
      window.dispatchEvent(new CustomEvent('compagnon:send-draft'))
    } catch {
      /* ignore */
    }
    return
  }
  if (a.kind !== 'agir' || !a.sourceText) return
  nextBusy.value = a.id
  addUserMessage(`Agir · ${a.label}`)
  try {
    const { proposal, reason } = await proposeAction(a.sourceText)
    if (!proposal) {
      addMessage({
        role: 'assistant',
        content: reason || 'Aucune action sûre.',
        source: 'agir',
      })
    } else {
      addMessage({
        role: 'assistant',
        content: proposal.summary || a.label,
        source: 'agir',
        actionProposal: proposal,
        actionSourceText: a.sourceText,
      })
    }
  } catch (e) {
    addMessage({
      role: 'assistant',
      content: String(e?.message || e),
      source: 'error',
    })
  } finally {
    nextBusy.value = ''
  }
}
</script>

<template>
  <div
    v-if="current"
    class="my-3 max-w-2xl rounded-2xl border border-white/10 bg-slate-900/80 backdrop-blur-xl p-3 shadow-lg shadow-black/40 text-xs animate-slide-up"
    :data-phase="current.phase"
  >
    <!-- En-tête activité -->
    <div class="flex items-center justify-between gap-2">
      <button
        type="button"
        class="flex items-center gap-2 text-left cursor-pointer hover:text-white transition-colors min-w-0"
        @click="toggleActivityOpen"
      >
        <span class="text-slate-500 font-mono text-[10px] transition-transform duration-150" :class="{ '-rotate-90': !current.open }">▾</span>
        <span class="font-bold text-slate-200 truncate">{{ current.title }}</span>
        <div class="hidden sm:flex items-center gap-1">
          <span
            v-for="t in current.tools"
            :key="t"
            class="text-[9px] font-mono text-slate-400 px-1.5 py-0.2 rounded border border-white/10 bg-white/5"
          >{{ t }}</span>
        </div>
      </button>

      <button
        type="button"
        class="text-slate-500 hover:text-slate-300 px-1.5 py-0.5 rounded text-[11px] cursor-pointer"
        title="Masquer"
        @click="clearActivity"
      >Masquer</button>
    </div>

    <!-- Journal de bord de l'activité -->
    <div v-if="current.open" class="mt-2.5 rounded-xl border border-white/5 bg-slate-950/80 p-2.5 max-h-36 overflow-y-auto scrollbar-custom font-mono text-[11px] leading-relaxed">
      <div
        v-for="(line, i) in current.lines"
        :key="i"
        :class="lineClass(line.level)"
        class="break-all whitespace-pre-wrap"
      >
        {{ line.text }}
      </div>
    </div>

    <!-- Phase / état actif -->
    <div class="mt-2 flex items-center justify-between gap-2 text-[11px]">
      <div class="flex items-center gap-2">
        <span
          v-if="current.phase === 'running' || current.phase === 'planning'"
          class="h-2 w-2 rounded-full bg-cyan-400 animate-pulse-soft"
        />
        <span
          v-else-if="current.phase === 'done'"
          class="h-2 w-2 rounded-full bg-emerald-400"
        />
        <span
          v-else-if="current.phase === 'error'"
          class="h-2 w-2 rounded-full bg-rose-400"
        />
        <span
          class="font-medium"
          :class="{
            'text-cyan-300': current.phase === 'running' || current.phase === 'planning',
            'text-emerald-400': current.phase === 'done',
            'text-rose-400': current.phase === 'error',
            'text-slate-400': !['running', 'planning', 'done', 'error'].includes(current.phase)
          }"
        >
          {{ current.phaseLabel }}
        </span>
      </div>

      <!-- Actions de suite (quickNext) -->
      <div v-if="quickNext.length" class="flex items-center gap-1.5 flex-wrap">
        <button
          v-for="a in quickNext"
          :key="a.id"
          type="button"
          class="px-2 py-0.5 rounded-lg text-[10px] font-semibold text-emerald-300 bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/30 transition-all cursor-pointer disabled:opacity-40"
          :disabled="!!nextBusy"
          @click="runQuick(a)"
        >
          {{ nextBusy === a.id ? '…' : a.label }}
        </button>
      </div>
    </div>
  </div>
</template>

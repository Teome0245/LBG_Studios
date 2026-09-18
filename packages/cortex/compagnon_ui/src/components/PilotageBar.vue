<script setup>
import { ref } from 'vue'
import { PILOTAGE_BAR } from '@/lib/pilotageActions'
import { proposeAction } from '@/lib/agir'
import { useChat } from '@/composables/useChat'
import {
  startActivity,
  activityLog,
  endActivity,
} from '@/composables/useActivity'

const emit = defineEmits(['ask'])

const { addUserMessage, addMessage } = useChat()
const busy = ref('')

async function runAgir(action) {
  if (!action?.sourceText || busy.value) return
  busy.value = action.id
  startActivity(`Pilotage · ${action.label}`, ['agir', 'pilotage'])
  activityLog(action.sourceText.slice(0, 120))
  addUserMessage(`Agir · ${action.label}`)
  try {
    const { proposal, reason } = await proposeAction(action.sourceText)
    if (!proposal) {
      activityLog(reason || 'aucune action', 'warn')
      endActivity('error')
      addMessage({
        role: 'assistant',
        content: reason || 'Aucune action sûre reconnue.',
        source: 'agir',
      })
      return
    }
    activityLog(`${proposal.capability || 'ok'}`, 'ok')
    endActivity('done', 'Carte prête — Dry-run / Réel')
    addMessage({
      role: 'assistant',
      content: proposal.summary || action.label,
      source: 'agir',
      actionProposal: proposal,
      actionSourceText: action.sourceText,
    })
  } catch (e) {
    endActivity('error', String(e?.message || e))
    addMessage({
      role: 'assistant',
      content: `Pilotage impossible : ${e?.message || e}`,
      source: 'error',
    })
  } finally {
    busy.value = ''
  }
}

function onClick(action) {
  if (action.kind === 'link' && action.href) {
    window.open(action.href, '_blank', 'noopener,noreferrer')
    return
  }
  if (action.kind === 'ask' && action.prompt) {
    emit('ask', action.prompt)
    return
  }
  if (action.kind === 'agir') {
    runAgir(action)
  }
}
</script>

<template>
  <div class="flex flex-wrap items-center gap-1.5 px-2 py-1 border-b border-white/5" role="toolbar" aria-label="Pilotage studio">
    <span class="text-[9px] font-bold tracking-widest uppercase text-slate-400 mr-1 select-none">
      Actions rapides
    </span>

    <button
      v-for="a in PILOTAGE_BAR"
      :key="a.id"
      type="button"
      class="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-medium text-slate-200 bg-white/5 hover:bg-white/10 border border-white/10 hover:border-emerald-500/30 transition-all duration-150 cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed active:scale-95"
      :class="{
        'hover:border-teal-400/40': a.kind === 'link',
        'hover:border-amber-400/40': a.kind === 'ask'
      }"
      :disabled="!!busy"
      :title="a.hint || a.label"
      @click="onClick(a)"
    >
      <span class="text-[11px] font-semibold">{{ busy === a.id ? '…' : a.label }}</span>
      <span v-if="a.hint" class="text-[9px] font-mono text-slate-400 opacity-75 hidden md:inline">{{ a.hint }}</span>
    </button>

    <div class="flex-1"></div>

    <button
      type="button"
      class="inline-flex items-center gap-1 text-[10px] font-mono text-slate-400 hover:text-slate-200 bg-slate-900/60 border border-white/10 rounded-md px-2 py-0.5 cursor-pointer hover:border-white/20 transition-colors"
      title="Ouvrir la palette de commandes (Ctrl+K)"
      @click="$emit('ask', '')"
    >
      <span>Palette</span>
      <kbd class="text-[9px] bg-white/5 px-1 py-0.2 rounded border border-white/10">⌘K</kbd>
    </button>
  </div>
</template>

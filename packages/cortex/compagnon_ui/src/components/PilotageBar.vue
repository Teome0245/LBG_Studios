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
  <div class="pilotage-bar" role="toolbar" aria-label="Pilotage studio">
    <span class="pilotage-label">Pilotage</span>
    <button
      v-for="a in PILOTAGE_BAR"
      :key="a.id"
      type="button"
      class="pilotage-btn"
      :class="{ 'is-link': a.kind === 'link', 'is-ask': a.kind === 'ask' }"
      :disabled="!!busy"
      :title="a.hint || a.label"
      @click="onClick(a)"
    >
      <span class="pilotage-btn-title">{{ busy === a.id ? '…' : a.label }}</span>
      <span v-if="a.hint" class="pilotage-btn-hint">{{ a.hint }}</span>
    </button>
    <span class="pilotage-hint-kbd" title="Palette de commandes">Ctrl+K</span>
  </div>
</template>

<style scoped>
.pilotage-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.35rem;
  padding: 0.15rem 0.35rem 0.35rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  margin-bottom: 0.15rem;
}
.pilotage-label {
  font-size: 0.58rem;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #5eead4;
  margin-right: 0.25rem;
}
.pilotage-btn {
  display: inline-flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.05rem;
  padding: 0.28rem 0.55rem;
  border-radius: 0.55rem;
  border: 1px solid rgba(45, 212, 191, 0.28);
  background: rgb(15 23 42 / 0.65);
  color: #e2e8f0;
  cursor: pointer;
  text-align: left;
}
.pilotage-btn:hover:not(:disabled) {
  border-color: rgba(45, 212, 191, 0.55);
  background: rgb(45 212 191 / 0.1);
}
.pilotage-btn:disabled {
  opacity: 0.45;
  cursor: default;
}
.pilotage-btn.is-link {
  border-color: rgba(148, 163, 184, 0.25);
}
.pilotage-btn.is-ask {
  border-color: rgba(251, 191, 36, 0.3);
}
.pilotage-btn-title {
  font-size: 0.68rem;
  font-weight: 700;
  line-height: 1.2;
}
.pilotage-btn-hint {
  font-size: 0.55rem;
  font-family: ui-monospace, monospace;
  color: #64748b;
}
.pilotage-hint-kbd {
  margin-left: auto;
  font-size: 0.55rem;
  font-family: ui-monospace, monospace;
  color: #64748b;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 0.3rem;
  padding: 0.12rem 0.35rem;
}
</style>

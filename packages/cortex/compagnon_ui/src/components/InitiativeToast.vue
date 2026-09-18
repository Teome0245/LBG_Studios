<script setup>
import { ref } from 'vue'
import { useInitiative } from '@/composables/useInitiative'
import { useChat } from '@/composables/useChat'
import { proposeAction } from '@/lib/agir'

const { current, dismiss, discussText, proposing } = useInitiative()
const { addUserMessage, addMessage } = useChat()
const busyId = ref('')

function discuss() {
  const msg = current.value?.message || 'initiative'
  addUserMessage(`À propos de ton initiative : « ${msg} »`)
  addMessage({
    role: 'assistant',
    content: discussText(),
    source: 'initiative',
    state: 'orchestrateur-happy',
  })
  dismiss(2) // snooze 2h après discussion
}

/** Prépare une carte Agir (proposal réelle) sans exécuter. */
async function runAgir(intent) {
  if (!intent?.sourceText || proposing.value) return
  busyId.value = intent.id || 'agir'
  proposing.value = true
  const text = intent.sourceText
  addUserMessage(`Agir · ${intent.label || text}`)
  try {
    const { proposal, reason } = await proposeAction(text)
    if (!proposal) {
      addMessage({
        role: 'assistant',
        content: reason || 'Aucune action sûre reconnue pour cette initiative.',
        source: 'agir',
      })
    } else {
      addMessage({
        role: 'assistant',
        content: proposal.summary || intent.label || 'Proposition prête — Dry-run puis Réel.',
        source: 'agir',
        actionProposal: proposal,
        actionSourceText: text,
      })
    }
    dismiss(6) // snooze 6h après Agir réussi
  } catch (e) {
    addMessage({
      role: 'assistant',
      content: `Proposition impossible : ${e?.message || e}`,
      source: 'error',
    })
  } finally {
    proposing.value = false
    busyId.value = ''
  }
}
</script>

<template>
  <Transition name="init-fade">
    <div
      v-if="current"
      class="initiative-toast"
      role="status"
      aria-live="polite"
    >
      <div class="initiative-head">
        <span class="initiative-dot"></span>
        <span class="initiative-label">Suggestion</span>
        <span v-if="current.kind" class="initiative-kind">{{ current.kind }}</span>
        <button
          type="button"
          class="initiative-close"
          title="Ignorer (snooze 4h)"
          @click="dismiss(4)"
        >✕</button>
      </div>

      <p class="initiative-msg">{{ current.message }}</p>

      <div v-if="current.intents?.length" class="initiative-intents">
        <button
          v-for="it in current.intents"
          :key="it.id"
          type="button"
          class="btn-agir"
          :disabled="!!busyId"
          @click="runAgir(it)"
        >
          <span class="btn-agir-title">{{ busyId === it.id ? '…' : it.label }}</span>
          <span v-if="it.hint" class="btn-agir-hint">{{ it.hint }}</span>
        </button>
      </div>

      <div class="initiative-actions">
        <button type="button" class="btn-ghost" @click="discuss">Détails</button>
        <button type="button" class="btn-ghost" @click="dismiss(4)">Ignorer</button>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.initiative-toast {
  position: fixed;
  right: 6.5rem;
  bottom: 6rem;
  z-index: 60;
  max-width: min(20rem, calc(100vw - 3rem));
  padding: 0.85rem 1rem;
  border-radius: 1.25rem;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(15, 23, 42, 0.96);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.6), 0 0 1px rgba(255, 255, 255, 0.2);
  color: #e2e8f0;
}
@media (max-width: 640px) {
  .initiative-toast {
    right: 1rem;
    bottom: 7.5rem;
  }
}
.initiative-head {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  margin-bottom: 0.35rem;
}
.initiative-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #38bdf8;
  box-shadow: 0 0 8px #38bdf8;
}
.initiative-label {
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #38bdf8;
}
.initiative-kind {
  font-size: 0.6rem;
  font-family: ui-monospace, monospace;
  color: #94a3b8;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 0.35rem;
  padding: 0.05rem 0.35rem;
  background: rgba(255, 255, 255, 0.03);
}
.initiative-close {
  margin-left: auto;
  border: none;
  background: transparent;
  color: #64748b;
  cursor: pointer;
  font-size: 0.75rem;
  padding: 0.1rem 0.3rem;
  border-radius: 0.25rem;
  line-height: 1;
}
.initiative-close:hover {
  color: #e2e8f0;
  background: rgba(255, 255, 255, 0.08);
}
.initiative-msg {
  margin: 0;
  font-size: 0.82rem;
  line-height: 1.4;
  color: #f1f5f9;
}
.initiative-intents {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  margin-top: 0.65rem;
}
.btn-agir {
  text-align: left;
  width: 100%;
  padding: 0.45rem 0.65rem;
  border-radius: 0.65rem;
  border: 1px solid rgba(16, 185, 129, 0.35);
  background: rgba(16, 185, 129, 0.12);
  color: #ecfdf5;
  cursor: pointer;
  transition: all 0.15s ease;
}
.btn-agir:hover:not(:disabled) {
  background: rgba(16, 185, 129, 0.22);
  border-color: rgba(16, 185, 129, 0.55);
}
.btn-agir:disabled {
  opacity: 0.45;
  cursor: default;
}
.btn-agir-title {
  display: block;
  font-size: 0.75rem;
  font-weight: 700;
}
.btn-agir-hint {
  display: block;
  font-size: 0.6rem;
  color: #94a3b8;
  margin-top: 0.05rem;
  font-family: ui-monospace, monospace;
}
.initiative-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin-top: 0.6rem;
}
.btn-ghost {
  font-size: 0.68rem;
  font-weight: 600;
  padding: 0.25rem 0.55rem;
  border-radius: 0.5rem;
  background: transparent;
  color: #94a3b8;
  border: 1px solid rgba(255, 255, 255, 0.1);
  cursor: pointer;
  transition: all 0.15s ease;
}
.btn-ghost:hover {
  color: #e2e8f0;
  border-color: rgba(255, 255, 255, 0.2);
  background: rgba(255, 255, 255, 0.04);
}
.init-fade-enter-active,
.init-fade-leave-active {
  transition: opacity 0.2s cubic-bezier(0.16, 1, 0.3, 1), transform 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}
.init-fade-enter-from,
.init-fade-leave-to {
  opacity: 0;
  transform: translateY(6px) scale(0.97);
}
</style>

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
  dismiss()
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
    dismiss()
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
        <span class="initiative-label">Je vois</span>
        <span v-if="current.kind" class="initiative-kind">{{ current.kind }}</span>
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

      <p class="initiative-hint">Agir = propose → Dry-run → Réel · jamais d’auto-exec.</p>
      <div class="initiative-actions">
        <button type="button" class="btn-ghost" @click="discuss">Expliquer</button>
        <button type="button" class="btn-ghost" @click="dismiss">Ignorer</button>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.initiative-toast {
  position: fixed;
  right: 1rem;
  bottom: 6.5rem;
  z-index: 60;
  max-width: min(22rem, calc(100vw - 2rem));
  padding: 0.85rem 1rem;
  border-radius: 1rem;
  border: 1px solid rgba(45, 212, 191, 0.35);
  background: rgb(2 6 23 / 0.94);
  box-shadow: 0 12px 40px rgb(0 0 0 / 0.45);
  color: #e2e8f0;
}
.initiative-head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.4rem;
  margin-bottom: 0.35rem;
}
.initiative-label {
  font-size: 0.65rem;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #5eead4;
}
.initiative-kind {
  font-size: 0.65rem;
  font-family: ui-monospace, monospace;
  color: #94a3b8;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 0.35rem;
  padding: 0.05rem 0.35rem;
}
.initiative-msg {
  margin: 0;
  font-size: 0.875rem;
  line-height: 1.4;
  color: #f1f5f9;
}
.initiative-intents {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  margin-top: 0.75rem;
}
.btn-agir {
  text-align: left;
  width: 100%;
  padding: 0.45rem 0.65rem;
  border-radius: 0.65rem;
  border: 1px solid rgba(16, 185, 129, 0.45);
  background: rgb(16 185 129 / 0.15);
  color: #ecfdf5;
  cursor: pointer;
}
.btn-agir:hover:not(:disabled) {
  background: rgb(16 185 129 / 0.28);
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
  margin-top: 0.1rem;
  font-family: ui-monospace, monospace;
}
.initiative-hint {
  margin: 0.45rem 0 0;
  font-size: 0.65rem;
  color: #64748b;
}
.initiative-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 0.55rem;
}
.btn-ghost {
  font-size: 0.7rem;
  font-weight: 600;
  padding: 0.35rem 0.7rem;
  border-radius: 0.6rem;
  background: transparent;
  color: #94a3b8;
  border: 1px solid rgba(255, 255, 255, 0.12);
  cursor: pointer;
}
.btn-ghost:hover {
  color: #e2e8f0;
  border-color: rgba(255, 255, 255, 0.25);
}
.init-fade-enter-active,
.init-fade-leave-active {
  transition: opacity 0.22s ease, transform 0.22s ease;
}
.init-fade-enter-from,
.init-fade-leave-to {
  opacity: 0;
  transform: translateY(8px);
}
</style>

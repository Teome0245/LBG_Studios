<script setup>
import { useInitiative } from '@/composables/useInitiative'
import { useChat } from '@/composables/useChat'

const { current, dismiss, discussText } = useInitiative()
const { addUserMessage, addMessage } = useChat()

function discuss() {
  const msg = current.value?.message || 'initiative'
  addUserMessage(`À propos de ton initiative : « ${msg} » — que proposes-tu (sans exécuter) ?`)
  addMessage({
    role: 'assistant',
    content: discussText(),
    source: 'initiative',
    state: 'orchestrateur-happy',
  })
  dismiss()
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
        <span class="initiative-label">Initiative</span>
        <span v-if="current.kind" class="initiative-kind">{{ current.kind }}</span>
      </div>
      <p class="initiative-msg">{{ current.message }}</p>
      <p class="initiative-hint">Proposition seule — aucune action auto (quota strict).</p>
      <div class="initiative-actions">
        <button type="button" class="btn-primary" @click="discuss">Discuter</button>
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
.initiative-hint {
  margin: 0.4rem 0 0;
  font-size: 0.65rem;
  color: #64748b;
}
.initiative-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 0.75rem;
}
.btn-primary {
  font-size: 0.7rem;
  font-weight: 700;
  padding: 0.35rem 0.7rem;
  border-radius: 0.6rem;
  background: rgb(16 185 129 / 0.9);
  color: #020617;
  border: none;
  cursor: pointer;
}
.btn-primary:hover {
  background: #34d399;
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

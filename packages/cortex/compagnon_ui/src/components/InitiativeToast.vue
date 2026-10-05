<script setup>
import { ref } from 'vue'
import { useInitiative } from '@/composables/useInitiative'
import { useChat } from '@/composables/useChat'
import { proposeAction } from '@/lib/agir'
import { spawnTeamL1, teamObjectiveFromInitiative } from '@/lib/teamSpawn'
import { setMandate } from '@/lib/mandate'
import { getStudioGoal } from '@/lib/studioGoal'

const { current, dismiss, discussText, proposing, selfLine, studioGoal } = useInitiative()
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
  dismiss(2, 'discuss')
}

function pickMandate(intent) {
  if (!intent?.mandatePick || !intent.mandateScope || proposing.value) return
  setMandate([intent.mandateScope])
  studioGoal.value = getStudioGoal()
  addUserMessage(`Mandat · ${intent.label}`)
  addMessage({
    role: 'assistant',
    content:
      `OK — je veille prioritairement « ${intent.label} » pour ~4 h` +
      ` (objectif · ${studioGoal.value?.goal?.title || intent.label}).` +
      `\nJe proposerai des actions dans ce périmètre ; Garde infra reste prioritaire.`,
    source: 'mandate',
    state: 'orchestrateur-happy',
  })
  dismiss(6, 'accept')
}

/** Prépare une carte Agir (proposal réelle) sans exécuter. */
async function runAgir(intent) {
  if (intent?.mandatePick) {
    pickMandate(intent)
    return
  }
  if (!intent?.sourceText || proposing.value) return
  if (intent.teamSpawn) {
    await runTeam(intent)
    return
  }
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
      dismiss(2, 'dismiss')
    } else {
      addMessage({
        role: 'assistant',
        content: proposal.summary || intent.label || 'Proposition prête — Dry-run puis Réel (contre-pouvoir).',
        source: 'agir',
        actionProposal: proposal,
        actionSourceText: text,
      })
      dismiss(6, 'accept')
    }
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

/** Délègue une tâche Team L1 (create + run si possible). */
async function runTeam(intent) {
  if (proposing.value) return
  busyId.value = intent?.id || 'team'
  proposing.value = true
  const objective = teamObjectiveFromInitiative(
    current.value?.message,
    intent?.teamObjective,
  )
  addUserMessage(`Team L1 · ${intent?.label || 'délégation'}`)
  try {
    const out = await spawnTeamL1({
      objective,
      role: intent?.teamRole || 'qa',
      context: { initiative_id: current.value?.id || '' },
      run: true,
    })
    if (!out.ok) {
      addMessage({
        role: 'assistant',
        content: `Team L1 impossible : ${out.error || 'erreur'}`,
        source: 'error',
      })
      dismiss(2, 'dismiss')
    } else {
      const runNote = out.run_error
        ? ` Créée (${out.id}) — run : ${out.run_error} (file Team / Pilot).`
        : ` Tâche ${out.id} · ${out.status || 'queued/run'}.`
      addMessage({
        role: 'assistant',
        content:
          `J’ai délégué à la Team (${out.role}) : « ${objective.slice(0, 160)} ».${runNote}` +
          `\nSuivi : Pilot #/team — contre-pouvoir Agir reste pour le Réel desktop.`,
        source: 'team',
      })
      dismiss(6, 'accept')
    }
  } catch (e) {
    addMessage({
      role: 'assistant',
      content: `Team L1 erreur : ${e?.message || e}`,
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
        <span class="initiative-label">{{
          current.spontaneous ? 'Spontané'
          : current.offerType === 'mandat' ? 'Mandat'
          : current.offerType === 'garde' ? 'Garde'
          : current.offerType === 'studio' ? 'Studio'
          : 'Suggestion'
        }}</span>
        <span v-if="current.goal?.title" class="initiative-goal">{{ current.goal.title }}</span>
        <span v-else-if="current.offerType" class="initiative-kind">{{ current.offerType }}</span>
        <span v-else-if="current.kind" class="initiative-kind">{{ current.kind }}</span>
        <button
          type="button"
          class="initiative-close"
          title="Ignorer (snooze 4h)"
          @click="dismiss(4, 'dismiss')"
        >✕</button>
      </div>

      <p class="initiative-msg">{{ current.message }}</p>
      <p v-if="selfLine" class="initiative-self">{{ selfLine }}</p>

      <div v-if="current.intents?.length" class="initiative-intents">
        <button
          v-for="it in (current.offerType === 'mandat' ? current.intents : current.intents.slice(0, 2))"
          :key="it.id"
          type="button"
          class="btn-agir"
          :class="{ 'btn-team': it.teamSpawn, 'btn-mandate': it.mandatePick }"
          :disabled="!!busyId"
          @click="runAgir(it)"
        >
          <span class="btn-agir-title">{{ busyId === it.id ? '…' : it.label }}</span>
          <span v-if="it.hint" class="btn-agir-hint">{{ it.hint }}</span>
        </button>
      </div>

      <div class="initiative-actions">
        <button type="button" class="btn-ghost" @click="discuss">Détails</button>
        <button
          v-if="current.offerType !== 'mandat'"
          type="button"
          class="btn-ghost"
          :disabled="!!busyId"
          @click="runTeam({ id: 'team_default', label: 'Team L1', teamSpawn: true })"
        >Team L1</button>
        <button type="button" class="btn-ghost" @click="dismiss(4, 'dismiss')">Ignorer</button>
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
.initiative-kind,
.initiative-goal {
  font-size: 0.6rem;
  font-family: ui-monospace, monospace;
  color: #94a3b8;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 0.35rem;
  padding: 0.05rem 0.35rem;
  background: rgba(255, 255, 255, 0.03);
  max-width: 9rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.initiative-goal {
  color: #5eead4;
  border-color: rgba(45, 212, 191, 0.25);
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
.initiative-self {
  margin: 0.35rem 0 0;
  font-size: 0.65rem;
  line-height: 1.3;
  color: #94a3b8;
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
.btn-agir.btn-team {
  border-color: rgba(56, 189, 248, 0.4);
  background: rgba(14, 165, 233, 0.12);
}
.btn-agir.btn-team:hover:not(:disabled) {
  background: rgba(14, 165, 233, 0.22);
  border-color: rgba(56, 189, 248, 0.6);
}
.btn-agir.btn-mandate {
  border-color: rgba(45, 212, 191, 0.4);
  background: rgba(13, 148, 136, 0.14);
}
.btn-agir.btn-mandate:hover:not(:disabled) {
  background: rgba(13, 148, 136, 0.24);
  border-color: rgba(45, 212, 191, 0.55);
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

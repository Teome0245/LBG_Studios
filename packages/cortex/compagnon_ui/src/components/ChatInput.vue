<script setup>
import { ref, watch } from 'vue'
import { useChat } from '../composables/useChat.js'
import { useApi } from '../composables/useApi.js'
import { useLayout } from '../composables/useLayout.js'
import { hasTeamMention, resolveAgentForPrompt } from '../lib/teamMentions.js'
import { proposeAction } from '@/lib/agir'

const AGENT_KEY = 'lbg_orch_input_agent'
const MODEL_KEY = 'lbg_orch_input_model'
const PROFILE_KEY = 'lbg_orch_input_profile'

const input = ref('')
const { addUserMessage, addMessage, loadConversations, draftPrompt, mentionInsert } = useChat()
const { sendPrompt } = useApi()
const { chatInputOffsetClass } = useLayout()
const loading = ref(false)
const proposing = ref(false)

function loadSel(key, fallback) {
  try {
    return localStorage.getItem(key) || fallback
  } catch {
    return fallback
  }
}

const selectedAgent = ref(loadSel(AGENT_KEY, 'auto'))
const selectedModel = ref(loadSel(MODEL_KEY, 'auto'))
const selectedProfile = ref(loadSel(PROFILE_KEY, 'compagnon'))

watch(selectedAgent, (v) => {
  try { localStorage.setItem(AGENT_KEY, v) } catch { /* */ }
})
watch(selectedModel, (v) => {
  try { localStorage.setItem(MODEL_KEY, v) } catch { /* */ }
})
watch(selectedProfile, (v) => {
  try { localStorage.setItem(PROFILE_KEY, v) } catch { /* */ }
})

const offsetClass = chatInputOffsetClass

const agentOptions = [
  { value: 'auto', label: 'Auto' },
  { value: 'team', label: 'Team' },
  { value: 'cursor', label: 'Cursor' },
  { value: 'tools', label: 'Diagnostic' },
]

const modelOptions = [
  { value: 'auto', label: 'Auto' },
  { value: 'fast', label: 'Fast' },
  { value: 'balanced', label: 'Balanced' },
  { value: 'smart', label: 'Smart' },
]

const profileOptions = [
  { value: 'compagnon', label: 'Compagnon' },
  { value: 'jarvis', label: 'Jarvis' },
  { value: 'mother', label: 'Mother' },
  { value: 'kit', label: 'Kit' },
  { value: 'hal', label: 'HAL' },
  { value: 'chaleureux', label: 'Chaleureux' },
  { value: 'neutre', label: 'Neutre' },
]

watch(draftPrompt, (v) => {
  if (v) {
    input.value = v
    draftPrompt.value = ''
  }
})

watch(mentionInsert, (v) => {
  if (!v) return
  const token = String(v).trim()
  mentionInsert.value = ''
  if (!token) return
  const cur = input.value
  if (cur.includes(token)) return
  const trimmed = cur.trimEnd()
  input.value = trimmed ? `${trimmed} ${token} ` : `${token} `
  // Clic roster Team → bascule Agent=Team
  if (hasTeamMention(token) || hasTeamMention(input.value)) {
    selectedAgent.value = 'team'
  }
})

const send = async () => {
  if (!input.value.trim() || loading.value || proposing.value) return

  const userMsg = input.value
  const agent = resolveAgentForPrompt(selectedAgent.value, userMsg)
  if (agent === 'team' && selectedAgent.value === 'auto') {
    selectedAgent.value = 'team'
  }
  addUserMessage(userMsg)
  input.value = ''
  loading.value = true

  try {
    const backendResponse = await sendPrompt(userMsg, {
      agent,
      model: selectedModel.value,
      profile: selectedProfile.value,
      mode: 'auto',
    })
    addMessage(backendResponse)
    loadConversations()
  } catch (e) {
    console.error('Error sending message:', e)
  } finally {
    loading.value = false
  }
}

/** Agir : propose une action Pilot (sans exécuter) → carte Dry-run / Réel. */
const propose = async () => {
  if (!input.value.trim() || loading.value || proposing.value) return
  const userMsg = input.value.trim()
  addUserMessage(userMsg)
  input.value = ''
  proposing.value = true
  try {
    const { proposal, reason } = await proposeAction(userMsg)
    if (!proposal) {
      addMessage({
        role: 'assistant',
        content: reason || 'Aucune action sûre reconnue. Reformule (ex. « ouvre Notepad », « cherche Cursor AI »).',
        source: 'agir',
        state: 'orchestrateur-happy',
      })
      return
    }
    addMessage({
      role: 'assistant',
      content: proposal.summary || 'Proposition prête — dry-run puis réel si OK.',
      source: 'agir',
      actionProposal: proposal,
      actionSourceText: userMsg,
    })
  } catch (e) {
    addMessage({
      role: 'assistant',
      content: `Proposition impossible : ${e?.message || e}`,
      source: 'error',
    })
  } finally {
    proposing.value = false
  }
}
</script>

<template>
  <div
    class="fixed bottom-0 right-0 p-4 sm:p-8 flex justify-center bg-gradient-to-t from-slate-950 via-slate-950/90 to-transparent z-10 transition-all duration-300"
    :class="offsetClass"
  >
    <div class="w-full max-w-4xl glass-card rounded-3xl p-2.5 shadow-2xl border-white/20 flex flex-col gap-2">
      <div class="flex flex-wrap items-center gap-2 px-2 pt-0.5">
        <label class="flex items-center gap-1.5 text-[10px] uppercase tracking-wider text-slate-500">
          Agent
          <select
            v-model="selectedAgent"
            class="bg-slate-900/80 border border-white/10 rounded-lg px-2 py-1 text-xs text-slate-200 focus:outline-none focus:border-emerald-500/40"
          >
            <option v-for="o in agentOptions" :key="o.value" :value="o.value">{{ o.label }}</option>
          </select>
        </label>
        <label class="flex items-center gap-1.5 text-[10px] uppercase tracking-wider text-slate-500">
          Mode
          <select
            v-model="selectedModel"
            class="bg-slate-900/80 border border-white/10 rounded-lg px-2 py-1 text-xs text-slate-200 focus:outline-none focus:border-emerald-500/40"
          >
            <option v-for="o in modelOptions" :key="o.value" :value="o.value">{{ o.label }}</option>
          </select>
        </label>
        <label class="flex items-center gap-1.5 text-[10px] uppercase tracking-wider text-slate-500">
          Persona
          <select
            v-model="selectedProfile"
            class="bg-slate-900/80 border border-white/10 rounded-lg px-2 py-1 text-xs text-slate-200 focus:outline-none focus:border-emerald-500/40"
          >
            <option v-for="o in profileOptions" :key="o.value" :value="o.value">{{ o.label }}</option>
          </select>
        </label>
      </div>

      <div class="flex items-end gap-2 sm:gap-3">
        <textarea
          v-model="input"
          rows="1"
          class="flex-1 bg-transparent border-none focus:ring-0 text-slate-100 placeholder-slate-500 text-sm py-3 px-4 resize-none overflow-hidden max-h-48 scrollbar-custom"
          placeholder="Parle au Compagnon… ou Agir pour une action poste"
          @keydown.enter.exact.prevent="send"
          @input="$event.target.style.height = 'auto'; $event.target.style.height = $event.target.scrollHeight + 'px'"
        />

        <button
          type="button"
          title="Proposer une action (dry-run / réel ensuite)"
          @click="propose"
          :disabled="!input.trim() || loading || proposing"
          class="h-10 px-3 flex-shrink-0 flex items-center justify-center rounded-2xl border border-cyan-500/40 text-cyan-200 text-[11px] font-bold uppercase tracking-wider hover:bg-cyan-500/15 disabled:opacity-30 disabled:grayscale transition-all active:scale-95"
        >
          {{ proposing ? '…' : 'Agir' }}
        </button>

        <button
          type="button"
          @click="send"
          :disabled="!input.trim() || loading || proposing"
          class="h-10 w-10 flex-shrink-0 flex items-center justify-center rounded-2xl bg-emerald-500 hover:bg-emerald-400 disabled:opacity-30 disabled:grayscale transition-all shadow-lg active:scale-90"
        >
          <svg v-if="!loading" xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-slate-900" viewBox="0 0 20 20" fill="currentColor">
            <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
          </svg>
          <svg v-else class="animate-spin h-5 w-5 text-slate-900" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
textarea {
  line-height: 1.5;
}
</style>

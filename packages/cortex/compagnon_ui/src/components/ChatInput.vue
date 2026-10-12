<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { useChat } from '../composables/useChat.js'
import { useApi } from '../composables/useApi.js'
import { useLayout } from '../composables/useLayout.js'
import { resolveAgentForPrompt } from '../lib/teamMentions.js'
import { proposeAction } from '@/lib/agir'
import {
  isRealizeRequest,
  suggestionsFromHistory,
  isDesktopish,
} from '@/lib/realizeSuggestions'
import {
  startActivity,
  activityLog,
  activityPhase,
  endActivity,
} from '@/composables/useActivity'
import {
  wantsMissionNotify,
  requestNotify,
  listWatches,
  watchMission,
  ackNotifyMessage,
  fetchCampusSnapshot,
} from '@/lib/missionWatch'
import PilotagePalette from './PilotagePalette.vue'

/** Arme / ré-arme le watch sur la mission Campus *ouverte* (évite un vieux id notified). */
async function ensureMissionWatchArmed() {
  const snap = await fetchCampusSnapshot().catch(() => null)
  const mid = String(snap?.status?.mission?.id || '').trim()
  if (mid) {
    return watchMission({
      missionId: mid,
      objective: String(snap?.status?.mission?.objective || '').slice(0, 240),
      taskIds: Array.isArray(snap?.status?.mission?.task_ids)
        ? snap.status.mission.task_ids
        : [],
      notify: true,
    })
  }
  return requestNotify() || listWatches()[0] || null
}

const AGENT_KEY = 'lbg_orch_input_agent'
const MODEL_KEY = 'lbg_orch_input_model'
const PROFILE_KEY = 'lbg_orch_input_profile'

const input = ref('')
const pendingImages = ref([])
const fileInputRef = ref(null)
const { addUserMessage, addMessage, loadConversations, draftPrompt, mentionInsert, messages } =
  useChat()
const { sendPrompt } = useApi()
const { chatInputOffsetClass } = useLayout()
const loading = ref(false)
const proposing = ref(false)

const MAX_IMAGES = 3
const MAX_IMAGE_BYTES = 4 * 1024 * 1024

function readFileAsDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result || ''))
    reader.onerror = () => reject(reader.error || new Error('lecture fichier'))
    reader.readAsDataURL(file)
  })
}

async function addImageFiles(fileList) {
  const files = Array.from(fileList || []).filter((f) => f && f.type && f.type.startsWith('image/'))
  for (const file of files) {
    if (pendingImages.value.length >= MAX_IMAGES) break
    if (file.size > MAX_IMAGE_BYTES) {
      addMessage({
        role: 'assistant',
        content: `Image trop lourde (${file.name}) — max 4 Mo.`,
        source: 'error',
      })
      continue
    }
    try {
      const dataUrl = await readFileAsDataUrl(file)
      if (dataUrl) pendingImages.value = [...pendingImages.value, dataUrl]
    } catch (e) {
      addMessage({
        role: 'assistant',
        content: `Impossible de lire ${file.name} : ${e?.message || e}`,
        source: 'error',
      })
    }
  }
}

function onPickFiles(ev) {
  const files = ev?.target?.files
  if (files?.length) addImageFiles(files)
  if (ev?.target) ev.target.value = ''
}

function onPaste(ev) {
  const items = ev?.clipboardData?.items
  if (!items) return
  const files = []
  for (const item of items) {
    if (item.type?.startsWith('image/')) {
      const f = item.getAsFile()
      if (f) files.push(f)
    }
  }
  if (files.length) {
    ev.preventDefault()
    addImageFiles(files)
  }
}

function removePendingImage(idx) {
  pendingImages.value = pendingImages.value.filter((_, i) => i !== idx)
}

function clearPendingImages() {
  pendingImages.value = []
}

const canSend = () =>
  Boolean(input.value.trim() || pendingImages.value.length) && !loading.value && !proposing.value


function loadSel(key, fallback) {
  try {
    return localStorage.getItem(key) || fallback
  } catch {
    return fallback
  }
}

const selectedAgent = ref(loadSel(AGENT_KEY, 'auto'))
// Ancien sticky Team (auto→team) cassait le chat : reset soft au chargement
if (selectedAgent.value === 'team') {
  selectedAgent.value = 'auto'
  try {
    localStorage.setItem(AGENT_KEY, 'auto')
  } catch {
    /* ignore */
  }
}
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

function onSendDraftEvent() {
  setTimeout(() => {
    if (input.value.trim()) send()
  }, 40)
}

onMounted(() => {
  window.addEventListener('compagnon:send-draft', onSendDraftEvent)
})
onUnmounted(() => {
  window.removeEventListener('compagnon:send-draft', onSendDraftEvent)
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
  // @mention Team → ce tour part en Team via resolveAgentForPrompt (auto),
  // sans verrouiller le sélecteur (sinon chat identité cassé ensuite).
})

const send = async () => {
  if (!canSend()) return

  const userMsg = input.value
  const images = [...pendingImages.value]
  const agent = resolveAgentForPrompt(selectedAgent.value, userMsg)
  // Ne PAS coller Agent=Team après un seul tour auto/@mention :
  // sinon chaque message suivant est préfixé `team:` → agent.fallback.
  const displayText = userMsg.trim() || (images.length ? '(image jointe)' : '')
  addUserMessage(displayText, { images })
  input.value = ''
  clearPendingImages()

  // D6.5 — « retour quand Team a traité » : active le watch + ack (pas d'Agir)
  if (!images.length && wantsMissionNotify(userMsg)) {
    try {
      const hit = await ensureMissionWatchArmed()
      addMessage({
        role: 'assistant',
        content: ackNotifyMessage(hit),
        source: 'mission_watch',
      })
      return
    } catch (e) {
      console.warn('missionWatch', e)
      // tombe sur /ask — on ré-arme quand même après la réponse backend
    }
  }

  // Interaction : « réalise les points » → agir / enchaîner, pas un nouveau pavé
  if (!images.length && isRealizeRequest(userMsg)) {
    const suggestions = suggestionsFromHistory(messages.value)
    if (suggestions.length) {
      loading.value = true
      startActivity('Enchaîner points suggérés', ['realize', 'agir', 'ask'])
      activityLog(`Points trouvés · ${suggestions.length}`)
      try {
        await realizeSuggestions(suggestions, agent)
        activityPhase('planning')
        endActivity('done', 'OK · enchaînement terminé')
        loadConversations()
      } catch (e) {
        console.error('realize', e)
        endActivity('error', String(e?.message || e))
        addMessage({
          role: 'assistant',
          content: `Je n’ai pas pu enchaîner : ${e?.message || e}`,
          source: 'error',
        })
      } finally {
        loading.value = false
      }
      return
    }
  }

  loading.value = true
  startActivity(
    images.length ? 'Compagnon · vision' : 'Compagnon · réponse',
    [images.length ? 'vision' : 'ask', agent !== 'auto' ? agent : 'auto'].filter(Boolean)
  )
  activityLog(
    images.length
      ? `POST /vision-ask · ${images.length} image(s) · profile=${selectedProfile.value}`
      : `POST /ask/stream · agent=${agent} · profile=${selectedProfile.value}`
  )
  activityPhase('running', images.length ? 'Analyse image…' : 'Appel modèle (SSE)…')
  try {
    let backendResponse = await sendPrompt(userMsg, {
      agent,
      model: selectedModel.value,
      profile: selectedProfile.value,
      mode: 'auto',
      images,
    })
    const lat = backendResponse?.latency
    activityLog(
      `OK · ${backendResponse?.source || 'assistant'}${lat != null ? ` · ${Number(lat).toFixed(2)}s` : ''}${
        backendResponse?.model ? ` · ${backendResponse.model}` : ''
      }`,
      'ok'
    )
    if (backendResponse?.actionProposal) {
      activityLog('Carte Agir jointe', 'ok')
    }
    activityPhase('planning')
    // Si le backend a répondu mission_watch (ou intent suivi), armer le watch local
    if (
      backendResponse?.source === 'mission_watch' ||
      backendResponse?.mission_watch?.notify ||
      wantsMissionNotify(userMsg)
    ) {
      try {
        const hit = await ensureMissionWatchArmed()
        if (hit && backendResponse?.source === 'mission_watch') {
          backendResponse = {
            ...backendResponse,
            content: ackNotifyMessage(hit),
          }
        }
      } catch (e) {
        console.warn('missionWatch arm after ask', e)
      }
    }
    addMessage(backendResponse)
    endActivity('done')
    loadConversations()
  } catch (e) {
    console.error('Error sending message:', e)
    endActivity('error', String(e?.message || e))
  } finally {
    loading.value = false
  }
}

/** Transforme les suggestions du fil en cartes Agir ou en vrai tour de chat. */
async function realizeSuggestions(suggestions, agent) {
  const desktop = suggestions.filter(isDesktopish)
  const discuss = suggestions.filter((s) => !isDesktopish(s))

  activityLog(`Desktop · ${desktop.length} · discuss · ${discuss.length}`)

  addMessage({
    role: 'assistant',
    content:
      desktop.length || discuss.length
        ? `OK — j’enchaîne sur ${suggestions.length} point(s) du fil (pas un nouveau rapport). Dry-run / Réel pour le poste ; le reste part en question concrète.`
        : 'Je ne trouve pas de points actionnables dans le fil.',
    source: 'agir',
  })

  for (const text of desktop.slice(0, 3)) {
    proposing.value = true
    activityLog(`Agir propose · ${text.slice(0, 80)}`)
    try {
      const { proposal, reason } = await proposeAction(text)
      if (!proposal) {
        activityLog(`skip · ${reason || 'non reconnu'}`, 'warn')
        addMessage({
          role: 'assistant',
          content: `« ${text} » — ${reason || 'pas d’action poste reconnue.'}`,
          source: 'agir',
        })
      } else {
        activityLog(`carte · ${proposal.capability || proposal.summary || 'ok'}`, 'ok')
        addMessage({
          role: 'assistant',
          content: proposal.summary || text,
          source: 'agir',
          actionProposal: proposal,
          actionSourceText: text,
        })
      }
    } finally {
      proposing.value = false
    }
  }

  if (discuss.length) {
    const first = discuss[0]
    activityLog(`Ask · ${first.slice(0, 100)}`)
    activityPhase('running', 'Suite du fil…')
    addUserMessage(first)
    const backendResponse = await sendPrompt(first, {
      agent,
      model: selectedModel.value,
      profile: selectedProfile.value,
      mode: 'auto',
    })
    activityLog(`OK point 1/${discuss.length}`, 'ok')
    addMessage(backendResponse)

    if (discuss.length > 1) {
      activityLog(`Chips restantes · ${discuss.length - 1}`)
      addMessage({
        role: 'assistant',
        content: `Autres points (${discuss.length - 1}) — clique pour enchaîner :`,
        source: 'agir',
        followup: {
          steps: discuss.slice(1).map((reply) => ({
            env: 'go',
            label: reply.length > 48 ? `${reply.slice(0, 46)}…` : reply,
            reply,
          })),
        },
      })
    }
  }
}

/** Agir : propose une action Pilot (sans exécuter) → carte Dry-run / Réel. */
const propose = async () => {
  if (!input.value.trim() || loading.value || proposing.value) return
  const userMsg = input.value.trim()
  addUserMessage(userMsg)
  input.value = ''
  proposing.value = true
  startActivity('Agir · proposition', ['agir', 'pilot'])
  activityLog(`POST /action-proposal · ${userMsg.slice(0, 100)}`)
  try {
    const { proposal, reason } = await proposeAction(userMsg)
    if (!proposal) {
      activityLog(reason || 'aucune action', 'warn')
      endActivity('error', 'Pas de proposal')
      addMessage({
        role: 'assistant',
        content:
          (reason || 'Aucune action sûre reconnue.') +
          '\n\nEssaie Ctrl+K : Selfcheck LAN, mails, inventaire réseau, VGHD, Jobs L2, Cockpit…',
        source: 'agir',
        state: 'orchestrateur-happy',
      })
      return
    }
    activityLog(`${proposal.capability || 'ok'} · ${proposal.summary || ''}`.slice(0, 160), 'ok')
    endActivity('done', 'Carte Agir prête — Dry-run puis Réel')
    addMessage({
      role: 'assistant',
      content: proposal.summary || 'Proposition prête — dry-run puis réel si OK.',
      source: 'agir',
      actionProposal: proposal,
      actionSourceText: userMsg,
    })
  } catch (e) {
    endActivity('error', String(e?.message || e))
    addMessage({
      role: 'assistant',
      content: `Proposition impossible : ${e?.message || e}`,
      source: 'error',
    })
  } finally {
    proposing.value = false
  }
}

const paletteRef = ref(null)

/** Pilotage bar · ask → envoi direct ou ouverture palette si vide. */
function onPilotageAsk(prompt) {
  if (!prompt) {
    paletteRef.value?.openPalette()
    return
  }
  if (loading.value || proposing.value) return
  input.value = String(prompt)
  send()
}
</script>

<template>
  <div
    class="fixed bottom-0 right-0 p-3 sm:p-6 flex justify-center bg-gradient-to-t from-slate-950 via-slate-950/80 to-transparent z-20 transition-all duration-300 pointer-events-none"
    :class="offsetClass"
  >
    <div class="w-full max-w-4xl glass-card rounded-3xl p-3 shadow-2xl border border-white/15 flex flex-col gap-2 pointer-events-auto backdrop-blur-2xl">
      <PilotagePalette ref="paletteRef" @ask="onPilotageAsk" />

      <!-- Sélecteurs + ouverture palette (pas de barre d’actions rapides) -->
      <div class="flex flex-wrap items-center gap-2 px-1">
        <details class="group/settings flex-1 min-w-0">
          <summary class="text-[10px] uppercase tracking-wider text-slate-500 font-semibold cursor-pointer select-none list-none inline-flex items-center gap-1.5 hover:text-slate-300 [&::-webkit-details-marker]:hidden">
            <span>Réglages</span>
            <span class="normal-case tracking-normal font-mono text-slate-600 group-open/settings:hidden">agent · mode · persona</span>
          </summary>
          <div class="flex flex-wrap items-center gap-2 pt-1.5 text-xs">
            <label class="flex items-center gap-1.5 text-[10px] uppercase tracking-wider text-slate-400 font-semibold">
              Agent
              <select
                v-model="selectedAgent"
                class="bg-slate-900/90 border border-white/10 rounded-lg px-2 py-0.5 text-xs text-slate-200 focus:outline-none focus:border-emerald-500/50 cursor-pointer"
              >
                <option v-for="o in agentOptions" :key="o.value" :value="o.value">{{ o.label }}</option>
              </select>
            </label>
            <label class="flex items-center gap-1.5 text-[10px] uppercase tracking-wider text-slate-400 font-semibold">
              Mode
              <select
                v-model="selectedModel"
                class="bg-slate-900/90 border border-white/10 rounded-lg px-2 py-0.5 text-xs text-slate-200 focus:outline-none focus:border-emerald-500/50 cursor-pointer"
              >
                <option v-for="o in modelOptions" :key="o.value" :value="o.value">{{ o.label }}</option>
              </select>
            </label>
            <label class="flex items-center gap-1.5 text-[10px] uppercase tracking-wider text-slate-400 font-semibold">
              Persona
              <select
                v-model="selectedProfile"
                class="bg-slate-900/90 border border-white/10 rounded-lg px-2 py-0.5 text-xs text-slate-200 focus:outline-none focus:border-emerald-500/50 cursor-pointer"
              >
                <option v-for="o in profileOptions" :key="o.value" :value="o.value">{{ o.label }}</option>
              </select>
            </label>
          </div>
        </details>
        <button
          type="button"
          class="text-[10px] font-mono text-slate-500 hover:text-teal-300 border border-transparent hover:border-white/10 rounded-md px-1.5 py-0.5 cursor-pointer transition-colors"
          title="Palette de pilotage (Ctrl+K)"
          @click="paletteRef?.openPalette()"
        >
          <kbd class="text-[9px]">Ctrl+K</kbd>
        </button>
      </div>

      <!-- Aperçus images jointes -->
      <div v-if="pendingImages.length" class="flex flex-wrap items-center gap-2 px-1">
        <div
          v-for="(src, idx) in pendingImages"
          :key="idx"
          class="relative"
        >
          <img
            :src="src"
            alt="À envoyer"
            class="h-14 w-14 rounded-xl object-cover border border-white/15 shadow"
          />
          <button
            type="button"
            class="absolute -top-1.5 -right-1.5 h-5 w-5 rounded-full bg-slate-900 border border-white/20 text-[10px] text-slate-200 hover:bg-rose-600/80 cursor-pointer"
            title="Retirer"
            @click="removePendingImage(idx)"
          >×</button>
        </div>
        <button
          type="button"
          class="text-[10px] uppercase tracking-wider text-slate-500 hover:text-slate-300 cursor-pointer"
          @click="clearPendingImages"
        >Tout retirer</button>
      </div>

      <!-- Zone de texte et actions -->
      <div class="flex items-end gap-2 sm:gap-3 bg-slate-950/40 rounded-2xl p-1.5 border border-white/5 focus-within:border-white/15 transition-colors">
        <input
          ref="fileInputRef"
          type="file"
          accept="image/*"
          multiple
          class="hidden"
          @change="onPickFiles"
        />
        <button
          type="button"
          title="Joindre une image (analyse vision)"
          class="h-9 w-9 flex-shrink-0 flex items-center justify-center rounded-xl border border-white/10 text-slate-300 hover:bg-white/5 hover:border-emerald-500/40 disabled:opacity-30 transition-all cursor-pointer"
          :disabled="loading || proposing || pendingImages.length >= MAX_IMAGES"
          @click="fileInputRef?.click()"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
        </button>
        <textarea
          v-model="input"
          rows="1"
          class="flex-1 bg-transparent border-none focus:ring-0 text-slate-100 placeholder-slate-500 text-sm py-2 px-3 resize-none overflow-hidden max-h-48 scrollbar-custom"
          placeholder="Échanger… colle ou joins une image"
          @keydown.enter.exact.prevent="send"
          @paste="onPaste"
          @input="$event.target.style.height = 'auto'; $event.target.style.height = $event.target.scrollHeight + 'px'"
        />

        <button
          type="button"
          title="Proposer une action sous validation (dry-run puis réel)"
          @click="propose"
          :disabled="!input.trim() || loading || proposing"
          class="h-9 px-3 flex-shrink-0 flex items-center justify-center rounded-xl border border-cyan-500/40 text-cyan-300 text-[11px] font-bold uppercase tracking-wider hover:bg-cyan-500/15 disabled:opacity-30 disabled:grayscale transition-all active:scale-95 cursor-pointer"
        >
          <span v-if="!proposing">Agir</span>
          <svg v-else class="animate-spin h-3.5 w-3.5 text-cyan-300" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
        </button>

        <button
          type="button"
          @click="send"
          :disabled="!canSend()"
          class="h-9 w-9 flex-shrink-0 flex items-center justify-center rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:opacity-30 disabled:grayscale transition-all shadow-md active:scale-90 cursor-pointer"
          title="Envoyer (Entrée)"
        >
          <svg v-if="!loading" xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-white" viewBox="0 0 20 20" fill="currentColor">
            <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
          </svg>
          <svg v-else class="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
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

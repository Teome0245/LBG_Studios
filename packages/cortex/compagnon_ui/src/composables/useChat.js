import { ref } from 'vue'
import { http } from '@/api/http'
import { presenceTalk } from '@/lib/presence'
import { speakText } from '@/lib/tts'
import { watchMission } from '@/lib/missionWatch'

const STORAGE_KEY = 'lbg_orch_conversation_id'

const messages = ref([])
const pendingConfirmation = ref(null)
const conversationId = ref(null)
const conversations = ref([])
const historyLoaded = ref(false)
const draftPrompt = ref('')
/** Token @mention à injecter dans ChatInput (append, pas replace). */
const mentionInsert = ref('')

function newConversationId() {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return `orch-${crypto.randomUUID()}`
  }
  return `orch-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`
}

function loadStoredConversationId() {
  try {
    return localStorage.getItem(STORAGE_KEY) || newConversationId()
  } catch {
    return newConversationId()
  }
}

function persistConversationId(id) {
  try {
    localStorage.setItem(STORAGE_KEY, id)
  } catch {
    /* ignore */
  }
}

conversationId.value = loadStoredConversationId()
persistConversationId(conversationId.value)

function turnToMessage(turn) {
  const role = turn.role === 'user' ? 'user' : 'assistant'
  const state = role === 'user' ? 'user' : 'orchestrateur-happy'
  return {
    role,
    content: turn.content || '',
    source: turn.meta?.source || (role === 'user' ? 'user' : 'memory'),
    state,
  }
}

/** Champs d'une bulle assistant (communs /ask et flux SSE). */
const MESSAGE_FIELDS = [
  'content',
  'source',
  'model',
  'provider',
  'latency',
  'agent_action',
  'reflection',
  'timeline',
  'cursor',
  'followup',
  'multi_block',
  'tools',
  'approval',
  'campus_meta',
  'actionProposal',
  'actionSourceText',
  'context_journal',
  'jobContract',
]

function pickFields(msg) {
  const out = {}
  for (const key of MESSAGE_FIELDS) {
    if (msg[key] !== undefined) out[key] = msg[key]
  }
  return out
}

function stateFor(source) {
  if (source === 'agent' || source === 'tool_loop' || source === 'team') return 'agent-local'
  if (source === 'error') return 'orchestrateur-error'
  return 'orchestrateur-happy'
}

/** Dernière bulle servie par le flux SSE (fusion du /ask final, pas de doublon). */
let streamedMessage = null
let streamTimer = null

function clearStreamTimer() {
  if (streamTimer) {
    clearTimeout(streamTimer)
    streamTimer = null
  }
}

export function useChat() {
  /** Effets de bord d'une bulle assistant — partagés par /ask et par le flux SSE. */
  const runAssistantSideEffects = (msg) => {
    const { role, content, source, campus_meta, actionProposal } = msg

    // D6.5 — auto-watch mission Campus (retour à la clôture)
    if (role === 'assistant' && campus_meta && typeof campus_meta === 'object') {
      const mid = String(campus_meta.mission_id || campus_meta.id || '').trim()
      if (mid) {
        watchMission({
          missionId: mid,
          objective: String(campus_meta.objective || content || '').slice(0, 240),
          taskIds: Array.isArray(campus_meta.task_ids) ? campus_meta.task_ids : [],
          notify: true,
        })
      }
    }

    if (role === 'assistant' && content) {
      const mood =
        source === 'error' ? 'tense' : actionProposal ? 'curious' : source === 'agir' ? 'curious' : 'serene'
      presenceTalk(String(content).slice(0, 160), mood)
      if (source !== 'error') {
        void speakText(String(content)).catch(() => {
          /* best-effort TTS */
        })
      }
    }
  }

  const addMessage = (backendMessage) => {
    if (!backendMessage || typeof backendMessage !== 'object') {
      messages.value.push({
        role: 'assistant',
        content: '⚠️ Réponse backend invalide',
        source: 'error',
        state: 'orchestrateur-error',
      })
      return
    }

    // Bulle déjà rendue par le flux SSE (1.2) : on fusionne le payload final, sans doublon.
    if (backendMessage.__streamed) {
      if (streamedMessage && messages.value.includes(streamedMessage)) {
        const prev = String(streamedMessage.content || '')
        const next = backendMessage.content != null ? String(backendMessage.content) : ''
        const content = next.trim() ? next : prev.trim() ? prev : 'Réponse vide — réessaie.'
        const source =
          backendMessage.source && backendMessage.source !== 'streaming'
            ? backendMessage.source
            : streamedMessage.source && streamedMessage.source !== 'streaming'
              ? streamedMessage.source
              : 'assistant'
        Object.assign(streamedMessage, pickFields(backendMessage), {
          role: backendMessage.role || 'assistant',
          content,
          source,
          state: stateFor(source),
          streaming: false,
          streamPending: false,
          streamThinking: false,
        })
      } else if (String(backendMessage.content || '').trim()) {
        // Bulle SSE perdue (navigation) — afficher quand même la réponse
        const { __streamed: _s, ...rest } = backendMessage
        messages.value.push({
          ...pickFields(rest),
          role: rest.role || 'assistant',
          state: stateFor(rest.source),
          streaming: false,
        })
        runAssistantSideEffects({
          ...pickFields(rest),
          role: rest.role || 'assistant',
        })
      } else {
        // Orphelin vide : retirer toute bulle SSE fantôme encore marquée streaming
        for (let i = messages.value.length - 1; i >= 0; i -= 1) {
          const m = messages.value[i]
          if (m?.role === 'assistant' && (m.streaming || m.source === 'streaming') && !String(m.content || '').trim()) {
            messages.value.splice(i, 1)
          }
        }
      }
      return
    }

    const { role, agent_action } = backendMessage

    if (agent_action === 'confirmation') {
      pendingConfirmation.value = backendMessage
    }

    const message = {
      ...pickFields(backendMessage),
      role,
      state: stateFor(backendMessage.source),
    }

    messages.value.push(message)
    runAssistantSideEffects(message)
  }

  /* ---- Flux SSE (plan 1.2) : bulle progressive avant le payload complet ---- */

  const beginStream = () => {
    clearStreamTimer()
    const msg = {
      role: 'assistant',
      content: '',
      source: 'streaming',
      state: 'orchestrateur-happy',
      streaming: true,
      // Masqué les 300 ms premières (indicateur de réflexion discret ensuite)
      streamPending: true,
      streamThinking: false,
    }
    messages.value.push(msg)
    streamedMessage = msg
    streamTimer = setTimeout(() => {
      if (streamedMessage === msg && msg.streaming) {
        msg.streamPending = false
        msg.streamThinking = true
      }
    }, 300)
    return msg
  }

  const appendStream = (delta) => {
    const msg = streamedMessage
    if (!msg || !msg.streaming || !delta) return
    if (msg.streamPending) {
      msg.streamPending = false
      msg.streamThinking = false
    }
    msg.content += String(delta)
  }

  /** Fusionne le payload final dans la bulle ; renvoie le message à passer à addMessage. */
  const finishStream = (final) => {
    clearStreamTimer()
    const msg = streamedMessage
    const live = msg && messages.value.includes(msg)
    const payload = final && typeof final === 'object' ? final : { content: String(final ?? '') }
    // Ne jamais écraser les deltas avec un done vide / mal parsé (bulle « Terminé » sans texte).
    const fromDelta = live ? String(msg.content || '') : ''
    const fromPayload =
      payload.content != null
        ? String(payload.content)
        : payload.response != null
          ? String(payload.response)
          : payload.raw != null
            ? String(payload.raw)
            : ''
    let content = fromPayload.trim() ? fromPayload : fromDelta
    let source =
      payload.source ||
      (live && msg.source && msg.source !== 'streaming' ? msg.source : 'assistant')
    // Garde-fou : jamais laisser source=streaming ni bulle vide après « Terminé ».
    if (!source || source === 'streaming') source = 'assistant'
    if (!String(content || '').trim()) {
      const errBit = payload.error || payload.detail
      content = errBit
        ? `Erreur : ${errBit}`
        : 'Réponse vide — réessaie ; si ça revient, vérifie le flux SSE /ask/stream.'
      if (errBit) source = 'error'
    }
    const merged = {
      ...payload,
      role: payload.role || 'assistant',
      content,
      source,
    }
    if (!live) {
      // Fallback sans bulle (conversation changée, pas de flux) → chemin /ask normal.
      streamedMessage = null
      return merged
    }
    Object.assign(msg, pickFields(payload), merged, {
      state: stateFor(merged.source),
      streaming: false,
      streamPending: false,
      streamThinking: false,
      __streamed: true,
    })
    streamedMessage = msg
    runAssistantSideEffects(msg)
    return { ...merged, __streamed: true }
  }

  const failStream = (message) => {
    clearStreamTimer()
    const text = `Erreur : ${message}`
    const msg = streamedMessage
    if (!msg || !messages.value.includes(msg)) {
      return { role: 'assistant', content: text, source: 'error' }
    }
    Object.assign(msg, {
      content: text,
      source: 'error',
      state: 'orchestrateur-error',
      streaming: false,
      streamPending: false,
      streamThinking: false,
      __streamed: true,
    })
    streamedMessage = msg
    return { ...pickFields(msg), role: 'assistant', content: text, source: 'error', __streamed: true }
  }

  /** Retire la bulle SSE en cours (fallback vers POST /ask JSON). */
  const cancelStream = () => {
    clearStreamTimer()
    const msg = streamedMessage
    streamedMessage = null
    if (!msg) return
    const i = messages.value.indexOf(msg)
    if (i >= 0) messages.value.splice(i, 1)
  }

  const addUserMessage = (content, extras = {}) => {
    const images = Array.isArray(extras.images) ? extras.images.filter(Boolean) : []
    messages.value.push({
      role: 'user',
      content,
      images,
      state: 'user',
    })
  }

  const loadHistory = async (force = false) => {
    if (historyLoaded.value && !force) return
    historyLoaded.value = true
    const id = conversationId.value
    if (!id) return
    try {
      const { data } = await http.get(`/chat/context/${encodeURIComponent(id)}`)
      const turns = Array.isArray(data?.turns) ? data.turns : []
      messages.value = turns.map(turnToMessage)
    } catch {
      messages.value = []
    }
  }

  const loadConversations = async () => {
    try {
      const { data } = await http.get('/chat/conversations', { params: { limit: 40 } })
      conversations.value = Array.isArray(data?.conversations) ? data.conversations : []
    } catch {
      conversations.value = []
    }
  }

  const switchConversation = async (id) => {
    if (!id || id === conversationId.value) return
    conversationId.value = id
    persistConversationId(id)
    messages.value = []
    pendingConfirmation.value = null
    historyLoaded.value = false
    await loadHistory(true)
  }

  const queuePrompt = (text) => {
    if (text) draftPrompt.value = String(text)
  }

  const appendMention = (mention) => {
    const raw = String(mention || '').trim()
    if (!raw) return
    mentionInsert.value = raw.startsWith('@') ? raw : `@${raw}`
  }

  const startNewChat = () => {
    const id = newConversationId()
    conversationId.value = id
    persistConversationId(id)
    messages.value = []
    pendingConfirmation.value = null
    historyLoaded.value = true
    loadConversations()
  }

  /**
   * A2 — Respire : nouveau conversation_id (coupe short_ctx serveur),
   * garde mandat / objectif studio (localStorage). Pas de « Nouveau fil » vide :
   * on laisse un ack pour que l’utilisateur voie le contrat.
   */
  const breatheConversation = () => {
    clearStreamTimer()
    streamedMessage = null
    const id = newConversationId()
    conversationId.value = id
    persistConversationId(id)
    messages.value = [
      {
        role: 'assistant',
        content:
          'Fil compacté — on repart léger. Mandat et objectif studio restent actifs ; le pavé ops précédent n’entre plus dans le contexte.',
        source: 'breathe',
        state: 'orchestrateur-happy',
      },
    ]
    pendingConfirmation.value = null
    historyLoaded.value = true
    void loadConversations()
  }

  const archiveConversation = async (id) => {
    if (!id) return
    await http.post(`/chat/conversations/${encodeURIComponent(id)}/archive`)
    await loadConversations()
    if (conversationId.value === id) startNewChat()
  }

  const unarchiveConversation = async (id) => {
    if (!id) return
    await http.post(`/chat/conversations/${encodeURIComponent(id)}/unarchive`)
    await loadConversations()
  }

  const deleteConversation = async (id) => {
    if (!id) return
    await http.delete(`/chat/conversations/${encodeURIComponent(id)}`)
    await loadConversations()
    if (conversationId.value === id) startNewChat()
  }

  return {
    messages,
    conversationId,
    conversations,
    addMessage,
    addUserMessage,
    pendingConfirmation,
    loadHistory,
    loadConversations,
    switchConversation,
    startNewChat,
    breatheConversation,
    archiveConversation,
    unarchiveConversation,
    deleteConversation,
    draftPrompt,
    queuePrompt,
    mentionInsert,
    appendMention,
    beginStream,
    appendStream,
    finishStream,
    failStream,
    cancelStream,
  }
}

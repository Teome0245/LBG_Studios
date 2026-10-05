import { ref } from 'vue'
import { http } from '@/api/http'
import { presenceTalk } from '@/lib/presence'
import { speakText } from '@/lib/tts'

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

export function useChat() {
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

    const {
      role,
      content,
      source,
      model,
      provider,
      latency,
      agent_action,
      reflection,
      timeline,
      cursor,
      followup,
      multi_block,
      tools,
      approval,
      campus_meta,
      actionProposal,
      actionSourceText,
    } = backendMessage

    let state = 'orchestrateur-happy'

    if (source === 'agent' || source === 'tool_loop' || source === 'team') {
      state = 'agent-local'
    } else if (source === 'error') {
      state = 'orchestrateur-error'
    }

    if (agent_action === 'confirmation') {
      pendingConfirmation.value = backendMessage
    }

    messages.value.push({
      role,
      content,
      source,
      model,
      provider,
      latency,
      agent_action,
      reflection: reflection || null,
      timeline: Array.isArray(timeline) ? timeline : null,
      cursor: cursor || null,
      followup: followup || null,
      multi_block: multi_block || null,
      tools: tools || null,
      approval: approval || null,
      campus_meta: campus_meta || null,
      actionProposal: actionProposal || null,
      actionSourceText: actionSourceText || '',
      state,
    })

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
    archiveConversation,
    unarchiveConversation,
    deleteConversation,
    draftPrompt,
    queuePrompt,
    mentionInsert,
    appendMention,
  }
}

import { ref } from 'vue'
import { http } from '@/api/http'
import { useChat } from './useChat.js'

export function useApi() {
  const loading = ref(false)
  const error = ref(null)
  const { conversationId } = useChat()

  const sendPrompt = async (prompt, opts = {}) => {
    loading.value = true
    error.value = null

    try {
      const payload = {
        prompt,
        mode: opts.mode || 'auto',
        profile: opts.profile || 'compagnon',
        conversation_id: conversationId.value,
      }
      if (opts.agent && opts.agent !== 'auto') payload.agent = opts.agent
      if (opts.model && opts.model !== 'auto') payload.model = opts.model

      const response = await http.post('/ask', payload)

      const data = response.data

      if (data && typeof data === 'object' && data.response) {
        return data.response
      }

      return data
    } catch (err) {
      const message = err.response?.data?.detail || err.message || 'Erreur inconnue'
      error.value = message

      return {
        role: 'assistant',
        content: `Erreur : ${message}`,
        source: 'error',
        model: null,
        provider: null,
        latency: null,
        raw: null,
        agent_action: null,
      }
    } finally {
      loading.value = false
    }
  }

  return {
    loading,
    error,
    sendPrompt,
  }
}

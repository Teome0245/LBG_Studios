import { ref } from 'vue'
import { http } from '@/api/http'
import { useChat } from './useChat.js'

/** @param {string[]} images data URI ou base64 */
async function sendVisionAsk(prompt, images, opts = {}) {
  const res = await fetch('/api/pilot/vision-ask', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify({
      prompt: prompt || '',
      images,
      profile: opts.profile || 'compagnon',
      conversation_id: opts.conversationId || null,
    }),
  })
  const text = await res.text()
  let data = null
  try {
    data = text ? JSON.parse(text) : null
  } catch {
    data = null
  }
  if (!res.ok || !data) {
    throw new Error((data && (data.detail || data.error)) || `HTTP ${res.status}`)
  }
  if (data.ok === false) {
    const errContent = data.response?.content || data.error || 'Analyse image échouée'
    return typeof data.response === 'object' && data.response
      ? data.response
      : { role: 'assistant', content: errContent, source: 'error' }
  }
  return data.response || data
}

export function useApi() {
  const loading = ref(false)
  const error = ref(null)
  const { conversationId } = useChat()

  const sendPrompt = async (prompt, opts = {}) => {
    loading.value = true
    error.value = null

    try {
      const images = Array.isArray(opts.images) ? opts.images.filter(Boolean) : []
      if (images.length) {
        return await sendVisionAsk(prompt, images, {
          profile: opts.profile || 'compagnon',
          conversationId: conversationId.value,
        })
      }

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

  return { loading, error, sendPrompt }
}

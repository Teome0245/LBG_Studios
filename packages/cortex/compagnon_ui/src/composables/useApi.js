import { ref } from 'vue'
import { apiUrl, http } from '@/api/http'
import { readAskStream } from '@/lib/askStream'
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

function errorMessageFrom(err) {
  const status = err?.response?.status
  const timedOut = err?.code === 'ECONNABORTED' || /timeout/i.test(String(err?.message || ''))
  return (
    err?.response?.data?.detail ||
    (timedOut
      ? 'Délai dépassé (LLM local lent) — réessaie ; causerie → e2b/.110, léger → 2B/.111 (pas de Groq en LAB). Ctrl+K Selfcheck.'
      : status === 504
        ? '504 Gateway Timeout — Ollama trop lent ; vérifie .111 (2B) chaud ou .110 e2b.'
        : err?.message || 'Erreur inconnue')
  )
}

export function useApi() {
  const loading = ref(false)
  const error = ref(null)
  const {
    conversationId,
    beginStream,
    appendStream,
    finishStream,
    failStream,
    cancelStream,
  } = useChat()

  /** POST /ask classique (fallback si SSE indisponible). */
  const sendAskJson = async (payload) => {
    const response = await http.post('/ask', payload)
    const data = response.data
    if (data && typeof data === 'object' && data.response) return data.response
    return data
  }

  /**
   * Plan 1.2 — POST /ask/stream (SSE) : bulle progressive + thinking ≥300 ms.
   * Fallback JSON /ask si le flux n'est pas joignable (404/405/ancien backend).
   */
  const sendAskStream = async (payload) => {
    beginStream()
    let res
    try {
      res = await fetch(apiUrl('/ask/stream'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'text/event-stream',
        },
        body: JSON.stringify(payload),
      })
    } catch {
      cancelStream()
      return sendAskJson(payload)
    }

    const ctype = String(res.headers.get('content-type') || '')
    if (!res.ok || !ctype.includes('text/event-stream')) {
      cancelStream()
      return sendAskJson(payload)
    }

    let final = null
    let streamErr = null
    try {
      await readAskStream(res, {
        onEvent(event, data) {
          if (event === 'delta' && data?.content) appendStream(data.content)
          else if (event === 'done') final = data?.response ?? data
          else if (event === 'error') streamErr = data?.error || 'erreur flux'
        },
      })
    } catch (err) {
      return failStream(errorMessageFrom(err))
    }

    if (streamErr) return failStream(streamErr)
    return finishStream(final && typeof final === 'object' ? final : { content: String(final || '') })
  }

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

      // Force JSON (tests / debug) : opts.stream === false
      if (opts.stream === false) return await sendAskJson(payload)
      return await sendAskStream(payload)
    } catch (err) {
      const message = errorMessageFrom(err)
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

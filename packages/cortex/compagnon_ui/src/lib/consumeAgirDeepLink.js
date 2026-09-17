/**
 * Deep-link Electron / toast : `?stay=1&agir=<texte>&agir_label=<label>`
 * → même flux que le bouton Agir (proposal, pas d’auto-exec).
 */
import { proposeAction } from '@/lib/agir'
import { useChat } from '@/composables/useChat'

let consuming = false

function clearAgirParams() {
  try {
    const u = new URL(window.location.href)
    if (!u.searchParams.has('agir') && !u.searchParams.has('agir_label')) return
    u.searchParams.delete('agir')
    u.searchParams.delete('agir_label')
    const qs = u.searchParams.toString()
    const next = `${u.pathname}${qs ? `?${qs}` : ''}${u.hash || ''}`
    window.history.replaceState({}, '', next)
  } catch {
    /* ignore */
  }
}

/**
 * @returns {Promise<boolean>} true si une proposition a été tentée
 */
export async function consumeAgirDeepLink() {
  if (typeof window === 'undefined' || consuming) return false
  let text = ''
  let label = 'Initiative'
  try {
    const q = new URLSearchParams(window.location.search || '')
    text = String(q.get('agir') || '').trim()
    label = String(q.get('agir_label') || 'Initiative').trim() || 'Initiative'
  } catch {
    return false
  }
  if (!text) return false

  consuming = true
  clearAgirParams()
  const { addUserMessage, addMessage } = useChat()
  addUserMessage(`Agir · ${label}`)
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
        content: proposal.summary || `${label} — Dry-run puis Réel.`,
        source: 'agir',
        actionProposal: proposal,
        actionSourceText: text,
      })
    }
    return true
  } catch (e) {
    addMessage({
      role: 'assistant',
      content: `Proposition impossible : ${e?.message || e}`,
      source: 'error',
    })
    return true
  } finally {
    consuming = false
  }
}

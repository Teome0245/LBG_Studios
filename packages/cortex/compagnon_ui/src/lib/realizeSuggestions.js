/**
 * Interaction réelle : « réalise les points » → actions / re-prompts,
 * pas un nouveau pavé LLM ni un avatar.
 */

const REALIZE_RE =
  /\b(r[eé]alis[ee]?r?|fais|faites|ex[eé]cut[ee]?r?|lance|applique|encha[iî]ne|go)\b[\s\S]{0,48}\b(points?|sugg[eé]r\w*|suite|propos[eé]\w*|actions?)\b|\b(fais[- ]?le|vas[- ]?y|on\s+y\s+va|prends[- ]?les)\b/i

const DESKTOP_RE =
  /\b(ouvre|lance|d[eé]marre|ferme|notepad|firefox|chrome|cursor|explorateur|terminal|pilot\s*jobs?)\b/i

/**
 * @param {string} text
 */
export function isRealizeRequest(text) {
  return REALIZE_RE.test(String(text || ''))
}

/**
 * Extrait des suggestions actionnables depuis le dernier message assistant.
 * @param {string} content
 * @returns {string[]}
 */
export function extractSuggestions(content) {
  const raw = String(content || '')
  const out = []
  const seen = new Set()

  // Lignes « - "… » / « - « … » / puces avec guillemets
  const quoted = raw.matchAll(/[-•*]\s*[«"“']([^»"”']{8,160})[»"”']/g)
  for (const m of quoted) {
    push(out, seen, m[1])
  }

  // Lignes « Suite : » / suggestions en fin de message
  const lines = raw.split(/\n/)
  for (const line of lines) {
    const t = line.trim()
    if (/^(suis[- ]?je|veut[- ]?tu|souhaite)/i.test(t)) continue
    const m =
      t.match(/^[-•*]\s+(.+)$/) ||
      t.match(/^\d+[.)]\s+(.+)$/) ||
      t.match(/^[«"](.+)[»"]$/)
    if (!m) continue
    let s = m[1].replace(/^[«"“']|[»"”']$/g, '').trim()
    // Évite les titres de section
    if (s.length < 12 || s.length > 180) continue
    if (/^providers|^ollama|^faits|^audit/i.test(s)) continue
    if (/https?:\/\//i.test(s) && !DESKTOP_RE.test(s)) {
      // URL seule → pas une suggestion conversationnelle
    }
    push(out, seen, s)
  }

  // Phrases suggérées en italique / fin de message (« … » ou "…")
  const loose = raw.matchAll(/[«"]([^»"]{12,160})[»"]/g)
  for (const m of loose) {
    const s = m[1].trim()
    if (/^(https?:|192\.168)/i.test(s)) continue
    if (/\?$/.test(s) || /^(montre|quels?|ouvre|lance|fais)/i.test(s)) {
      push(out, seen, s)
    }
  }

  return out.slice(0, 5)
}

function push(out, seen, s) {
  const cleaned = String(s || '')
    .replace(/\s+/g, ' ')
    .trim()
  const key = cleaned.toLowerCase()
  if (!key || key.length < 12) return
  // Évite les sous-chaînes déjà couvertes (« montre l » vs phrase complète)
  for (const existing of seen) {
    if (existing.includes(key) || key.includes(existing)) {
      if (key.length <= existing.length) return
      // remplacer la plus courte
      const idx = out.findIndex((x) => x.toLowerCase() === existing)
      if (idx >= 0) out.splice(idx, 1)
      seen.delete(existing)
      break
    }
  }
  seen.add(key)
  out.push(cleaned)
}

/**
 * @param {Array<{ role?: string, content?: string, followup?: { steps?: Array<{ reply?: string, label?: string }> } }>} messages
 */
export function suggestionsFromHistory(messages) {
  const list = Array.isArray(messages) ? messages : []
  for (let i = list.length - 1; i >= 0; i--) {
    const m = list[i]
    if (!m || m.role === 'user') continue
    const fromFollowup = (m.followup?.steps || [])
      .map((s) => s.reply || s.label || '')
      .filter(Boolean)
    const fromText = extractSuggestions(m.content || '')
    const merged = []
    const seen = new Set()
    for (const s of [...fromFollowup, ...fromText]) {
      push(merged, seen, s)
    }
    if (merged.length) return merged
  }
  return []
}

export function isDesktopish(text) {
  return DESKTOP_RE.test(String(text || ''))
}

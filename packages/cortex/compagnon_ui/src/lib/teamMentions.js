/** Handles roster Team / Campus — alignés backend team_routing._TEAM_HANDLES */
export const TEAM_HANDLES = new Set([
  'themis',
  'argus',
  'hephaistos',
  'dedale',
  'vulcan',
  'iris',
  'hermes',
  'pygmalion',
  'choeur',
  'lia',
  'nix',
  'mira',
  'superviseur',
  'dialogue',
  'devops',
  'forge',
  'audit',
  'lyra',
])

const MENTION_RE = /(?:^|[^\w@])@([a-zA-Z0-9_-]+)/g

export function extractTeamMentions(text) {
  const found = []
  const seen = new Set()
  const s = String(text || '')
  let m
  MENTION_RE.lastIndex = 0
  while ((m = MENTION_RE.exec(s)) !== null) {
    const h = m[1].toLowerCase()
    if (TEAM_HANDLES.has(h) && !seen.has(h)) {
      seen.add(h)
      found.push(h)
    }
  }
  return found
}

export function hasTeamMention(text) {
  return extractTeamMentions(text).length > 0
}

/** Si agent=auto et @mention Team → force team. */
export function resolveAgentForPrompt(selectedAgent, prompt) {
  const sel = (selectedAgent || 'auto').toLowerCase()
  if (sel !== 'auto' && sel !== '') return sel
  if (hasTeamMention(prompt)) return 'team'
  return sel || 'auto'
}

import axios from 'axios'

const fromEnv = (import.meta.env.VITE_API_BASE_URL || '').trim().replace(/\/$/, '')

function resolveBaseURL() {
  if (fromEnv) return fromEnv
  if (import.meta.env.PROD) return '/api'
  return ''
}

export const apiBaseURL = resolveBaseURL()

/** Instance axios partagée (base URL = env, ou '' en dev pour proxy Vite, ou `/api` en prod). */
export const http = axios.create({
  baseURL: apiBaseURL,
  // Local LLM (gemma) peut prendre 30–90s + failover Groq — au-delà nginx 600s
  timeout: 180_000,
})

/** Préfixe les chemins comme axios pour `fetch`. */
export function apiUrl(path) {
  const p = path.startsWith('/') ? path : `/${path}`
  if (apiBaseURL) return `${apiBaseURL}${p}`
  return p
}

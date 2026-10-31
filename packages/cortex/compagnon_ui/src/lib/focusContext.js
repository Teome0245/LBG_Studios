/**
 * focusContext.js — Gestionnaire de conscience d'espace de travail (Focus Awareness).
 *
 * Maintient le contexte actif de l'utilisateur (coding, gamedev, terminal, gaming, browsing, idle)
 * transmis par compagnon-desktop ou l'agent local.
 */

let currentFocus = {
  category: 'general',
  attitude: 'serene',
  app: 'desktop',
  label: 'Activité bureau',
  ts: Date.now(),
}

const focusListeners = new Set()

export function setFocusContext(ctx) {
  if (!ctx || typeof ctx !== 'object') return
  currentFocus = {
    ...currentFocus,
    ...ctx,
    ts: Date.now(),
  }
  focusListeners.forEach((fn) => {
    try {
      fn(currentFocus)
    } catch {
      /* ignore */
    }
  })
}

export function getFocusContext() {
  return currentFocus
}

export function onFocusChange(fn) {
  if (typeof fn !== 'function') return () => {}
  focusListeners.add(fn)
  return () => focusListeners.delete(fn)
}

export function resetFocusContext() {
  currentFocus = {
    category: 'general',
    attitude: 'serene',
    app: 'desktop',
    label: 'Activité bureau',
    ts: Date.now(),
  }
}

// Initialisation automatique avec le pont Electron si disponible
if (typeof window !== 'undefined' && window.compagnonDesktop?.onFocusContext) {
  window.compagnonDesktop.onFocusContext((ctx) => {
    setFocusContext(ctx)
  })
}


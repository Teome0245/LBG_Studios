<script setup>
/**
 * Palette de pilotage (Ctrl+K / Ctrl+P) — lancer Agir / ask / Pilot
 * sans quitter le fil, style surface agent Cursor.
 */
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { PILOTAGE_BAR } from '@/lib/pilotageActions'
import { PILOT_NAV } from '@/lib/pilotLinks'
import { proposeAction } from '@/lib/agir'
import { useChat } from '@/composables/useChat'
import {
  startActivity,
  activityLog,
  endActivity,
} from '@/composables/useActivity'

const emit = defineEmits(['ask'])

const open = ref(false)
const query = ref('')
const active = ref(0)
const busy = ref('')
const inputEl = ref(null)
const { addUserMessage, addMessage } = useChat()

const EXTRA = [
  {
    id: 'pal_realize',
    label: 'Réalise la dernière idée',
    hint: 'ask · chaîne',
    kind: 'ask',
    prompt: 'réalise ça',
  },
  {
    id: 'pal_campus',
    label: 'Campus — file & agents',
    hint: 'ask',
    kind: 'ask',
    prompt: 'team: résumé campus, file active et agents dispo',
  },
]

const items = computed(() => {
  const q = query.value.trim().toLowerCase()
  const base = [
    ...PILOTAGE_BAR,
    ...EXTRA,
    ...PILOT_NAV.map((n) => ({
      id: `nav_${n.id}`,
      label: `Pilot · ${n.label}`,
      hint: 'lien',
      kind: 'link',
      href: n.href,
    })),
  ]
  if (!q) return base
  return base.filter((a) => {
    const hay = `${a.label} ${a.hint || ''} ${a.sourceText || ''} ${a.prompt || ''}`.toLowerCase()
    return hay.includes(q)
  })
})

watch(items, () => {
  active.value = 0
})

function openPalette() {
  open.value = true
  query.value = ''
  active.value = 0
  nextTick(() => inputEl.value?.focus())
}

function closePalette() {
  open.value = false
  query.value = ''
  busy.value = ''
}

function onKey(e) {
  const mod = e.ctrlKey || e.metaKey
  if (mod && (e.key === 'k' || e.key === 'K' || e.key === 'p' || e.key === 'P')) {
    e.preventDefault()
    if (open.value) closePalette()
    else openPalette()
    return
  }
  if (!open.value) return
  if (e.key === 'Escape') {
    e.preventDefault()
    closePalette()
    return
  }
  if (e.key === 'ArrowDown') {
    e.preventDefault()
    active.value = Math.min(active.value + 1, Math.max(0, items.value.length - 1))
    return
  }
  if (e.key === 'ArrowUp') {
    e.preventDefault()
    active.value = Math.max(active.value - 1, 0)
    return
  }
  if (e.key === 'Enter') {
    e.preventDefault()
    const a = items.value[active.value]
    if (a) run(a)
  }
}

onMounted(() => window.addEventListener('keydown', onKey))
onUnmounted(() => window.removeEventListener('keydown', onKey))

async function runAgir(action) {
  if (!action?.sourceText || busy.value) return
  busy.value = action.id
  startActivity(`Pilotage · ${action.label}`, ['agir', 'palette'])
  activityLog(action.sourceText.slice(0, 120))
  addUserMessage(`Agir · ${action.label}`)
  try {
    const { proposal, reason } = await proposeAction(action.sourceText)
    if (!proposal) {
      activityLog(reason || 'aucune action', 'warn')
      endActivity('error')
      addMessage({
        role: 'assistant',
        content: reason || 'Aucune action sûre reconnue.',
        source: 'agir',
      })
      return
    }
    activityLog(`${proposal.capability || 'ok'}`, 'ok')
    endActivity('done', 'Carte prête — Dry-run / Réel')
    addMessage({
      role: 'assistant',
      content: proposal.summary || action.label,
      source: 'agir',
      actionProposal: proposal,
      actionSourceText: action.sourceText,
    })
  } catch (e) {
    endActivity('error', String(e?.message || e))
    addMessage({
      role: 'assistant',
      content: `Pilotage impossible : ${e?.message || e}`,
      source: 'error',
    })
  } finally {
    busy.value = ''
    closePalette()
  }
}

function run(action) {
  if (!action || busy.value) return
  if (action.kind === 'link' && action.href) {
    window.open(action.href, '_blank', 'noopener,noreferrer')
    closePalette()
    return
  }
  if (action.kind === 'ask' && action.prompt) {
    emit('ask', action.prompt)
    closePalette()
    return
  }
  if (action.kind === 'agir') {
    runAgir(action)
  }
}
</script>

<template>
  <Teleport to="body">
    <div
      v-if="open"
      class="pal-backdrop"
      @click.self="closePalette"
    >
      <div
        class="pal-modal"
        role="dialog"
        aria-label="Pilotage studio"
      >
        <div class="pal-input-row">
          <span class="pal-kbd">⌘K</span>
          <input
            ref="inputEl"
            v-model="query"
            type="text"
            class="pal-input"
            placeholder="Pilotage — Agir, ask, Pilot…"
            autocomplete="off"
            spellcheck="false"
          />
        </div>
        <ul class="pal-list" role="listbox">
          <li
            v-for="(a, i) in items"
            :key="a.id"
            role="option"
            class="pal-item"
            :class="{ active: i === active, busy: busy === a.id }"
            :aria-selected="i === active"
            @mouseenter="active = i"
            @click="run(a)"
          >
            <span class="pal-item-label">{{ busy === a.id ? '…' : a.label }}</span>
            <span class="pal-item-meta">
              <span class="pal-kind">{{ a.kind }}</span>
              <span v-if="a.hint" class="pal-hint">{{ a.hint }}</span>
            </span>
          </li>
          <li v-if="!items.length" class="pal-empty">Aucune commande</li>
        </ul>
        <p class="pal-foot">
          <kbd>↑↓</kbd> naviguer · <kbd>↵</kbd> lancer · <kbd>esc</kbd> fermer
        </p>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.pal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 80;
  background: rgb(2 6 23 / 0.55);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: 12vh 1rem 2rem;
}
.pal-modal {
  width: min(32rem, 100%);
  border-radius: 0.85rem;
  border: 1px solid rgba(45, 212, 191, 0.28);
  background: rgb(15 23 42 / 0.96);
  box-shadow: 0 24px 64px rgb(0 0 0 / 0.45);
  overflow: hidden;
}
.pal-input-row {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  padding: 0.7rem 0.85rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}
.pal-kbd {
  font-size: 0.62rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  color: #5eead4;
  border: 1px solid rgba(45, 212, 191, 0.35);
  border-radius: 0.35rem;
  padding: 0.15rem 0.35rem;
  flex-shrink: 0;
}
.pal-input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  color: #f1f5f9;
  font-size: 0.92rem;
}
.pal-input::placeholder {
  color: #64748b;
}
.pal-list {
  list-style: none;
  margin: 0;
  padding: 0.35rem;
  max-height: 18rem;
  overflow: auto;
}
.pal-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.55rem 0.65rem;
  border-radius: 0.5rem;
  cursor: pointer;
  color: #e2e8f0;
}
.pal-item.active,
.pal-item:hover {
  background: rgb(45 212 191 / 0.12);
}
.pal-item.busy {
  opacity: 0.6;
}
.pal-item-label {
  font-size: 0.82rem;
  font-weight: 600;
}
.pal-item-meta {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  flex-shrink: 0;
}
.pal-kind {
  font-size: 0.58rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #5eead4;
  border: 1px solid rgba(45, 212, 191, 0.3);
  border-radius: 0.25rem;
  padding: 0.05rem 0.3rem;
}
.pal-hint {
  font-size: 0.62rem;
  font-family: ui-monospace, monospace;
  color: #64748b;
}
.pal-empty {
  padding: 1rem;
  text-align: center;
  color: #64748b;
  font-size: 0.8rem;
}
.pal-foot {
  margin: 0;
  padding: 0.45rem 0.85rem 0.65rem;
  font-size: 0.62rem;
  color: #64748b;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}
.pal-foot kbd {
  font-family: ui-monospace, monospace;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 0.25rem;
  padding: 0.05rem 0.25rem;
  margin: 0 0.1rem;
}
</style>

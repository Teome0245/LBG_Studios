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

defineExpose({ openPalette, closePalette })
</script>

<template>
  <Teleport to="body">
    <div
      v-if="open"
      class="fixed inset-0 z-[80] bg-slate-950/60 backdrop-blur-sm flex items-start justify-center p-4 sm:pt-24"
      @click.self="closePalette"
    >
      <div
        class="w-full max-w-xl rounded-2xl border border-white/15 bg-slate-900/95 shadow-2xl shadow-black/80 overflow-hidden backdrop-blur-xl animate-slide-up"
        role="dialog"
        aria-label="Pilotage studio"
      >
        <div class="flex items-center gap-3 px-4 py-3 border-b border-white/10 bg-white/5">
          <span class="text-[10px] font-mono font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/30 rounded px-1.5 py-0.5">
            ⌘K
          </span>
          <input
            ref="inputEl"
            v-model="query"
            type="text"
            class="flex-1 bg-transparent border-none outline-none text-slate-100 placeholder-slate-500 text-sm focus:ring-0"
            placeholder="Rechercher une action, question ou outil…"
            autocomplete="off"
            spellcheck="false"
          />
          <button
            type="button"
            class="text-xs text-slate-400 hover:text-slate-200 px-1.5 py-0.5 rounded border border-white/10"
            @click="closePalette"
          >Esc</button>
        </div>

        <ul class="max-h-80 overflow-y-auto scrollbar-custom p-2 space-y-1" role="listbox">
          <li
            v-for="(a, i) in items"
            :key="a.id"
            role="option"
            class="flex items-center justify-between gap-3 px-3 py-2.5 rounded-xl cursor-pointer text-slate-200 transition-all text-xs"
            :class="i === active ? 'bg-emerald-500/15 text-emerald-200 border-l-2 border-emerald-400' : 'hover:bg-white/5'"
            :aria-selected="i === active"
            @mouseenter="active = i"
            @click="run(a)"
          >
            <div class="flex items-center gap-2.5 min-w-0">
              <span class="font-medium truncate">{{ busy === a.id ? '…' : a.label }}</span>
            </div>

            <div class="flex items-center gap-2 shrink-0">
              <span class="text-[9px] uppercase tracking-wider font-bold text-slate-400 px-1.5 py-0.5 rounded border border-white/10 bg-white/5">
                {{ a.kind }}
              </span>
              <span v-if="a.hint" class="text-[10px] font-mono text-slate-500">
                {{ a.hint }}
              </span>
            </div>
          </li>

          <li v-if="!items.length" class="py-8 text-center text-slate-500 text-xs">
            Aucune commande correspondante.
          </li>
        </ul>

        <div class="px-4 py-2 border-t border-white/10 text-[10px] text-slate-500 flex items-center justify-between bg-white/2">
          <span><kbd class="font-mono bg-white/5 border border-white/10 px-1 py-0.5 rounded">↑↓</kbd> Naviguer</span>
          <span><kbd class="font-mono bg-white/5 border border-white/10 px-1 py-0.5 rounded">↵</kbd> Valider</span>
          <span><kbd class="font-mono bg-white/5 border border-white/10 px-1 py-0.5 rounded">Esc</kbd> Fermer</span>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useChat } from '../composables/useChat'

const {
  conversationId,
  conversations,
  loadConversations,
  switchConversation,
  startNewChat,
  archiveConversation,
  unarchiveConversation,
  deleteConversation,
} = useChat()

const route = useRoute()
const router = useRouter()
const pinnedIds = ref([])
const showArchived = ref(false)
const busyId = ref(null)

const PIN_KEY = 'lbg_orch_pinned_conversations'

function loadPinned() {
  try {
    const raw = localStorage.getItem(PIN_KEY)
    pinnedIds.value = raw ? JSON.parse(raw) : []
  } catch {
    pinnedIds.value = []
  }
}

function savePinned() {
  try {
    localStorage.setItem(PIN_KEY, JSON.stringify(pinnedIds.value))
  } catch {
    /* ignore */
  }
}

function isPinned(id) {
  return pinnedIds.value.includes(id)
}

function togglePin(id, event) {
  event?.stopPropagation()
  if (isPinned(id)) {
    pinnedIds.value = pinnedIds.value.filter((x) => x !== id)
  } else {
    pinnedIds.value = [...pinnedIds.value, id]
  }
  savePinned()
}

function isToday(iso) {
  if (!iso) return false
  const d = new Date(iso)
  const now = new Date()
  return d.toDateString() === now.toDateString()
}

function relativeAge(iso) {
  if (!iso) return ''
  const t = new Date(iso).getTime()
  if (Number.isNaN(t)) return ''
  const sec = Math.max(0, Math.floor((Date.now() - t) / 1000))
  if (sec < 60) return `${sec}s`
  const min = Math.floor(sec / 60)
  if (min < 60) return `${min}m`
  const h = Math.floor(min / 60)
  if (h < 24) return `${h}h`
  const d = Math.floor(h / 24)
  if (d < 7) return `${d}j`
  return new Date(iso).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short' })
}

function absoluteTitle(iso) {
  if (!iso) return ''
  try {
    return new Date(iso).toLocaleString('fr-FR')
  } catch {
    return iso
  }
}

const active = computed(() =>
  conversations.value.filter((c) => !c.archived)
)
const archived = computed(() =>
  conversations.value.filter((c) => c.archived)
)

const pinned = computed(() =>
  active.value.filter((c) => isPinned(c.id))
)
const today = computed(() =>
  active.value.filter((c) => !isPinned(c.id) && isToday(c.updated_at))
)
const older = computed(() =>
  active.value.filter((c) => !isPinned(c.id) && !isToday(c.updated_at))
)

function titleOf(c) {
  const t = (c.title || '').trim()
  if (!t || /^conversation$/i.test(t) || /^orch-/i.test(t)) {
    const preview = (c.preview || c.last_message || c.snippet || '').trim()
    if (preview) return preview.length > 42 ? `${preview.slice(0, 39)}…` : preview
    return 'Discussion'
  }
  return t.length > 42 ? `${t.slice(0, 39)}…` : t
}

async function onSelect(id) {
  if (id === conversationId.value) return
  await switchConversation(id)
  if (route.path !== '/') await router.push('/')
}

function onNew() {
  startNewChat()
  if (route.path !== '/') router.push('/')
}

async function onArchive(c, event) {
  event?.stopPropagation()
  busyId.value = c.id
  try {
    await archiveConversation(c.id)
  } finally {
    busyId.value = null
  }
}

async function onUnarchive(c, event) {
  event?.stopPropagation()
  busyId.value = c.id
  try {
    await unarchiveConversation(c.id)
  } finally {
    busyId.value = null
  }
}

async function onDelete(c, event) {
  event?.stopPropagation()
  const ok = window.confirm(`Supprimer définitivement « ${titleOf(c)} » ?`)
  if (!ok) return
  busyId.value = c.id
  try {
    await deleteConversation(c.id)
  } finally {
    busyId.value = null
  }
}

onMounted(() => {
  loadPinned()
  loadConversations()
})

watch(conversationId, () => {
  loadConversations()
})
</script>

<template>
  <div class="px-3 pb-3 space-y-3">
    <button
      type="button"
      class="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all hover:bg-white/5 text-slate-400 hover:text-white border border-white/5"
      @click="onNew"
    >
      <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
      </svg>
      New Chat
    </button>

    <section v-if="pinned.length">
      <h3 class="px-2 text-[10px] font-bold uppercase tracking-widest text-slate-500 mb-1">Épinglées</h3>
      <ul class="space-y-0.5">
        <li v-for="c in pinned" :key="c.id">
          <div
            class="w-full text-left px-2 py-1.5 rounded-md text-xs group cursor-pointer"
            :class="c.id === conversationId ? 'bg-emerald-500/15 text-emerald-300' : 'text-slate-400 hover:bg-white/5 hover:text-slate-200'"
            @click="onSelect(c.id)"
          >
            <div class="flex items-center gap-1">
              <span class="flex-1 truncate" :title="c.title">{{ titleOf(c) }}</span>
              <span class="text-[9px] font-mono text-slate-500 shrink-0" :title="absoluteTitle(c.updated_at)">{{ relativeAge(c.updated_at) }}</span>
            </div>
            <div class="flex gap-1 mt-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
              <button type="button" class="text-[9px] text-slate-500 hover:text-amber-300" title="Désépingler" @click="togglePin(c.id, $event)">★</button>
              <button type="button" class="text-[9px] text-slate-500 hover:text-sky-300" :disabled="busyId===c.id" @click="onArchive(c, $event)">Archiver</button>
              <button type="button" class="text-[9px] text-slate-500 hover:text-red-400" :disabled="busyId===c.id" @click="onDelete(c, $event)">Suppr.</button>
            </div>
          </div>
        </li>
      </ul>
    </section>

    <section v-if="today.length">
      <h3 class="px-2 text-[10px] font-bold uppercase tracking-widest text-slate-500 mb-1">Aujourd'hui</h3>
      <ul class="space-y-0.5">
        <li v-for="c in today" :key="c.id">
          <div
            class="w-full text-left px-2 py-1.5 rounded-md text-xs group cursor-pointer"
            :class="c.id === conversationId ? 'bg-emerald-500/15 text-emerald-300' : 'text-slate-400 hover:bg-white/5 hover:text-slate-200'"
            @click="onSelect(c.id)"
          >
            <div class="flex items-center gap-1">
              <span class="flex-1 truncate" :title="c.title">{{ titleOf(c) }}</span>
              <span class="text-[9px] font-mono text-slate-500 shrink-0" :title="absoluteTitle(c.updated_at)">{{ relativeAge(c.updated_at) }}</span>
            </div>
            <div class="flex gap-1 mt-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
              <button type="button" class="text-[9px] text-slate-500 hover:text-amber-300" @click="togglePin(c.id, $event)">☆</button>
              <button type="button" class="text-[9px] text-slate-500 hover:text-sky-300" :disabled="busyId===c.id" @click="onArchive(c, $event)">Archiver</button>
              <button type="button" class="text-[9px] text-slate-500 hover:text-red-400" :disabled="busyId===c.id" @click="onDelete(c, $event)">Suppr.</button>
            </div>
          </div>
        </li>
      </ul>
    </section>

    <section v-if="older.length">
      <h3 class="px-2 text-[10px] font-bold uppercase tracking-widest text-slate-500 mb-1">Plus ancien</h3>
      <ul class="space-y-0.5 max-h-48 overflow-y-auto scrollbar-custom">
        <li v-for="c in older" :key="c.id">
          <div
            class="w-full text-left px-2 py-1.5 rounded-md text-xs group cursor-pointer"
            :class="c.id === conversationId ? 'bg-emerald-500/15 text-emerald-300' : 'text-slate-400 hover:bg-white/5 hover:text-slate-200'"
            @click="onSelect(c.id)"
          >
            <div class="flex items-center gap-1">
              <span class="flex-1 truncate" :title="c.title">{{ titleOf(c) }}</span>
              <span class="text-[9px] font-mono text-slate-500 shrink-0" :title="absoluteTitle(c.updated_at)">{{ relativeAge(c.updated_at) }}</span>
            </div>
            <div class="flex gap-1 mt-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
              <button type="button" class="text-[9px] text-slate-500 hover:text-amber-300" @click="togglePin(c.id, $event)">☆</button>
              <button type="button" class="text-[9px] text-slate-500 hover:text-sky-300" :disabled="busyId===c.id" @click="onArchive(c, $event)">Archiver</button>
              <button type="button" class="text-[9px] text-slate-500 hover:text-red-400" :disabled="busyId===c.id" @click="onDelete(c, $event)">Suppr.</button>
            </div>
          </div>
        </li>
      </ul>
    </section>

    <section>
      <button
        type="button"
        class="px-2 text-[10px] font-bold uppercase tracking-widest text-slate-500 hover:text-slate-300"
        @click="showArchived = !showArchived"
      >
        Archivées ({{ archived.length }}) {{ showArchived ? '▾' : '▸' }}
      </button>
      <ul v-if="showArchived" class="space-y-0.5 mt-1 max-h-36 overflow-y-auto scrollbar-custom">
        <li v-for="c in archived" :key="c.id">
          <div
            class="w-full text-left px-2 py-1.5 rounded-md text-xs group cursor-pointer text-slate-500 hover:bg-white/5"
            @click="onSelect(c.id)"
          >
            <div class="flex items-center gap-1">
              <span class="flex-1 truncate opacity-70" :title="c.title">{{ titleOf(c) }}</span>
              <span class="text-[9px] font-mono shrink-0" :title="absoluteTitle(c.updated_at)">{{ relativeAge(c.updated_at) }}</span>
            </div>
            <div class="flex gap-1 mt-0.5 opacity-0 group-hover:opacity-100">
              <button type="button" class="text-[9px] hover:text-emerald-300" :disabled="busyId===c.id" @click="onUnarchive(c, $event)">Restaurer</button>
              <button type="button" class="text-[9px] hover:text-red-400" :disabled="busyId===c.id" @click="onDelete(c, $event)">Suppr.</button>
            </div>
          </div>
        </li>
        <li v-if="!archived.length" class="px-2 text-[10px] text-slate-600 italic">Aucune archive</li>
      </ul>
    </section>
  </div>
</template>

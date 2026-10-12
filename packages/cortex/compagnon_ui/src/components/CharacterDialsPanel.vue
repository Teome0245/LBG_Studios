<template>
  <aside
    v-if="open"
    class="character-dials glass-panel border-l border-white/5 flex flex-col h-full z-10 shrink-0 w-72 hidden lg:flex"
    aria-label="Caractère Compagnon (lab)"
  >
    <header class="px-3 py-2.5 border-b border-white/5 flex items-center justify-between gap-2">
      <div class="min-w-0">
        <h3 class="text-xs font-bold tracking-wide text-teal-300/90 uppercase">Caractère</h3>
        <p class="text-[10px] text-slate-500 truncate">Lab · 7 dials · sync serveur</p>
      </div>
      <button
        type="button"
        class="text-[10px] text-slate-400 hover:text-slate-200 px-1.5 py-0.5 rounded border border-transparent hover:border-white/10"
        title="Fermer"
        @click="close"
      >✕</button>
    </header>

    <div class="flex-1 overflow-y-auto px-3 py-3 space-y-3">
      <p class="text-[10px] text-slate-500 leading-relaxed">
        Personnalité = worldview studio. Caractère = expression (ces curseurs).
        Prod borne ego / piquant ; lab autorise un cran de plus.
      </p>

      <div
        v-for="def in DIAL_DEFS"
        :key="def.id"
        class="space-y-1"
      >
        <div class="flex items-center justify-between gap-2">
          <label class="text-[11px] font-semibold text-slate-300" :for="'dial-' + def.id">
            {{ def.label }}
          </label>
          <span class="font-mono text-[10px] text-slate-400">{{ pct(dials[def.id]) }}</span>
        </div>
        <input
          :id="'dial-' + def.id"
          type="range"
          min="0"
          max="100"
          step="5"
          class="w-full accent-teal-400"
          :value="Math.round(dials[def.id] * 100)"
          @input="onSlide(def.id, $event)"
        />
        <div class="flex justify-between text-[9px] text-slate-600 uppercase tracking-wider">
          <span>{{ def.low }}</span>
          <span>{{ def.high }}</span>
        </div>
      </div>
    </div>

    <footer class="px-3 py-2.5 border-t border-white/5 flex items-center gap-2">
      <button
        type="button"
        class="flex-1 text-[11px] font-semibold py-1.5 rounded-lg bg-teal-500/15 text-teal-200 border border-teal-500/30 hover:bg-teal-500/25 transition-colors"
        :disabled="saving"
        @click="save"
      >{{ saving ? '…' : 'Appliquer' }}</button>
      <button
        type="button"
        class="text-[11px] py-1.5 px-2 rounded-lg text-slate-400 hover:text-slate-200 border border-white/10"
        @click="reset"
      >Reset</button>
    </footer>
    <p v-if="status" class="px-3 pb-2 text-[10px]" :class="statusOk ? 'text-emerald-400/80' : 'text-amber-400/80'">
      {{ status }}
    </p>
  </aside>
</template>

<script setup>
import { onMounted, reactive, ref, watch } from 'vue'
import {
  DIAL_DEFS,
  getDials,
  setDials,
  resetDials,
  setPanelOpen,
  syncDialsToServer,
  hydrateDialsFromServer,
} from '../lib/characterDials.js'

const props = defineProps({
  open: { type: Boolean, default: false },
})

const emit = defineEmits(['close'])

const dials = reactive({ ...getDials() })
const saving = ref(false)
const status = ref('')
const statusOk = ref(true)

function pct(v) {
  return `${Math.round((Number(v) || 0) * 100)}%`
}

function onSlide(id, ev) {
  const n = Number(ev.target?.value)
  if (!Number.isFinite(n)) return
  dials[id] = Math.max(0, Math.min(1, n / 100))
  setDials({ ...dials })
}

function close() {
  setPanelOpen(false)
  emit('close')
}

async function save() {
  saving.value = true
  status.value = ''
  const local = setDials({ ...dials })
  Object.assign(dials, local)
  const res = await syncDialsToServer(local, { lab: true })
  saving.value = false
  statusOk.value = !!res.ok
  status.value = res.ok ? 'Dials appliqués (session serveur).' : `Local OK · sync API : ${res.error || res.status || 'ko'}`
}

function reset() {
  const d = resetDials()
  Object.assign(dials, d)
  status.value = 'Reset local.'
  statusOk.value = true
  syncDialsToServer(d, { lab: true })
}

watch(
  () => props.open,
  (v) => setPanelOpen(!!v),
)

onMounted(async () => {
  const remote = await hydrateDialsFromServer()
  Object.assign(dials, remote)
})
</script>

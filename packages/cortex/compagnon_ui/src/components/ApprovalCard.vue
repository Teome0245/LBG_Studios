<script setup>
import { ref, computed } from 'vue'
import { http } from '@/api/http'

const props = defineProps({
  approval: { type: Object, required: true },
})

const TOKEN_KEY = 'lbg_orch_team_approval_token'
const token = ref('')
const busyId = ref(null)
const statusById = ref({})

try {
  token.value = localStorage.getItem(TOKEN_KEY) || ''
} catch {
  /* ignore */
}

const tasks = computed(() =>
  Array.isArray(props.approval?.tasks) ? props.approval.tasks : []
)

function persistToken() {
  try {
    if (token.value) localStorage.setItem(TOKEN_KEY, token.value)
  } catch {
    /* ignore */
  }
}

function setStatus(taskId, text, ok = true) {
  statusById.value = {
    ...statusById.value,
    [taskId]: { text, ok },
  }
}

async function approve(task) {
  const tid = task.task_id
  if (!tid) return
  const tok = token.value.trim()
  if (!tok) {
    setStatus(tid, 'Token requis', false)
    return
  }
  persistToken()
  busyId.value = tid
  try {
    const { data } = await http.post(`/team/tasks/${encodeURIComponent(tid)}/approve`, {
      token: tok,
    })
    if (data?.ok === false) {
      setStatus(tid, data.error || 'Approbation KO', false)
    } else {
      setStatus(tid, `Approuvée · ${data?.status || 'ok'}`)
    }
  } catch (e) {
    setStatus(tid, e.response?.data?.detail || e.message || 'Erreur', false)
  } finally {
    busyId.value = null
  }
}

async function run(task) {
  const tid = task.task_id
  if (!tid) return
  const tok = token.value.trim()
  persistToken()
  busyId.value = tid
  try {
    const body = tok ? { approval_token: tok } : {}
    const { data } = await http.post(`/team/tasks/${encodeURIComponent(tid)}/run`, body)
    if (data?.ok === false) {
      setStatus(tid, data.error || 'Exécution KO', false)
    } else {
      setStatus(tid, `Exécutée · ${data?.status || 'ok'}`)
    }
  } catch (e) {
    setStatus(tid, e.response?.data?.detail || e.message || 'Erreur', false)
  } finally {
    busyId.value = null
  }
}
</script>

<template>
  <div
    v-if="tasks.length"
    class="mt-4 rounded-2xl border border-amber-500/30 bg-amber-500/10 px-3 py-3 space-y-3"
  >
    <div class="flex flex-wrap items-center justify-between gap-2">
      <p class="text-[11px] uppercase tracking-widest font-bold text-amber-300">
        {{ approval.title || 'Validation L2' }}
      </p>
      <a
        href="http://192.168.0.140:8080/#/team/office"
        target="_blank"
        rel="noopener noreferrer"
        class="text-[10px] text-amber-200/80 hover:text-amber-100 underline underline-offset-2"
      >Bureau Campus →</a>
    </div>
    <p v-if="approval.hint" class="text-[11px] text-slate-400">{{ approval.hint }}</p>

    <label class="block text-[10px] uppercase tracking-wider text-slate-500 mb-1">
      Token approbation
      <input
        v-model="token"
        type="password"
        autocomplete="off"
        placeholder="token L2"
        class="mt-1 w-full max-w-xs rounded-lg border border-white/15 bg-slate-950/80 px-2.5 py-1.5 text-xs text-slate-100 placeholder:text-slate-600 focus:outline-none focus:border-amber-500/40"
        @change="persistToken"
      />
    </label>

    <div
      v-for="t in tasks"
      :key="t.task_id"
      class="rounded-xl border border-white/10 bg-slate-950/40 px-3 py-2.5 space-y-2"
    >
      <div class="flex flex-wrap items-baseline gap-2 text-xs">
        <span class="font-semibold text-amber-100">{{ t.role_label || t.role || 'agent' }}</span>
        <span class="font-mono text-[10px] text-slate-500">{{ t.task_id }}</span>
        <span class="text-[10px] uppercase text-slate-500">{{ t.status }}</span>
      </div>
      <p class="text-xs text-slate-300 leading-snug">{{ t.objective }}</p>
      <div class="flex flex-wrap gap-2 items-center">
        <button
          type="button"
          class="px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-amber-500/90 text-slate-950 hover:bg-amber-400 disabled:opacity-40"
          :disabled="busyId === t.task_id"
          @click="approve(t)"
        >
          Approuver
        </button>
        <button
          type="button"
          class="px-2.5 py-1 rounded-lg text-[11px] font-semibold border border-emerald-500/40 text-emerald-300 hover:bg-emerald-500/15 disabled:opacity-40"
          :disabled="busyId === t.task_id"
          @click="run(t)"
        >
          Exécuter
        </button>
        <span
          v-if="statusById[t.task_id]"
          class="text-[10px] font-mono"
          :class="statusById[t.task_id].ok ? 'text-emerald-400' : 'text-red-400'"
        >{{ statusById[t.task_id].text }}</span>
      </div>
    </div>
  </div>
</template>

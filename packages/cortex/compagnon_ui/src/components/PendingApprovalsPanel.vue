<template>
  <div>
    <div class="flex items-center justify-between mb-2 gap-2">
      <h3 class="text-[11px] font-semibold uppercase opacity-60 tracking-widest">
        Approbations L2
      </h3>
      <span
        v-if="count > 0"
        class="text-[9px] font-mono px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300"
      >{{ count }}</span>
    </div>

    <div v-if="loading && !items.length" class="text-slate-500 italic text-[10px]">
      …
    </div>
    <div v-else-if="!items.length" class="text-slate-500 italic text-[10px]">
      Aucune en attente
    </div>
    <ul v-else class="space-y-1.5">
      <li
        v-for="t in items"
        :key="t.id"
        class="rounded-lg border border-amber-500/20 bg-amber-500/5 px-2 py-1.5 cursor-pointer hover:border-amber-500/40"
        :title="t.objective"
        @click="onSelect(t)"
      >
        <div class="flex justify-between gap-1 text-[10px]">
          <span class="font-semibold text-amber-100 truncate">{{ t.role_label || t.role }}</span>
          <span class="font-mono text-slate-500 shrink-0">{{ String(t.id || '').slice(0, 8) }}</span>
        </div>
        <p class="text-[10px] text-slate-400 truncate mt-0.5">{{ t.objective }}</p>
      </li>
    </ul>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import { http } from '@/api/http'
import { useChat } from '../composables/useChat'

const { queuePrompt } = useChat()

const items = ref([])
const count = ref(0)
const loading = ref(false)

function onSelect(t) {
  queuePrompt(
    `team: status orchestrateur et file Campus — tâche L2 ${t.id} (${t.role || '?'})`
  )
}

async function load() {
  loading.value = true
  try {
    const res = await http.get('/team/pending', { params: { limit: 8, _t: Date.now() } })
    items.value = Array.isArray(res.data?.tasks) ? res.data.tasks.slice(0, 5) : []
    count.value = Number(res.data?.count) || items.value.length
  } catch {
    items.value = []
    count.value = 0
  } finally {
    loading.value = false
  }
}

let intervalId
onMounted(() => {
  load()
  intervalId = setInterval(load, 20000)
})
onUnmounted(() => {
  if (intervalId) clearInterval(intervalId)
})
</script>

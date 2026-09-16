<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useChat } from '../composables/useChat'
import { useLayout } from '../composables/useLayout'

const { queuePrompt } = useChat()
const { monitorCollapsed, toggleMonitor } = useLayout()
const router = useRouter()
const hint = ref('')

function ensureMonitor() {
  if (monitorCollapsed.value) toggleMonitor()
}

function onNewAgent() {
  ensureMonitor()
  hint.value = 'Clique un agent du roster (ex. @iris) ou envoie la mission préremplie.'
  queuePrompt('@themis propose une mission Campus pour un nouvel agent / persona Studio')
  if (router.currentRoute.value.path !== '/') router.push('/')
}

function onCustomize() {
  hint.value = ''
  router.push('/lyra')
}
</script>

<template>
  <div class="space-y-1.5">
    <div class="flex gap-1.5">
      <button
        type="button"
        class="flex-1 text-[10px] font-semibold uppercase tracking-wider px-2 py-1.5 rounded-lg border border-violet-400/25 bg-violet-400/10 text-violet-200 hover:bg-violet-400/20 transition-colors"
        title="Mission Team pour un nouveau persona (pas de factory locale)"
        @click="onNewAgent"
      >
        New Agent
      </button>
      <button
        type="button"
        class="flex-1 text-[10px] font-semibold uppercase tracking-wider px-2 py-1.5 rounded-lg border border-sky-400/25 bg-sky-400/10 text-sky-200 hover:bg-sky-400/20 transition-colors"
        title="Personnalisation Lyra"
        @click="onCustomize"
      >
        Customize
      </button>
    </div>
    <p v-if="hint" class="text-[9px] text-slate-500 leading-snug">{{ hint }}</p>
    <p v-else class="text-[9px] text-slate-600 leading-snug">
      Studio : pas de factory d’agents — roster + @mention / Lyra.
    </p>
  </div>
</template>

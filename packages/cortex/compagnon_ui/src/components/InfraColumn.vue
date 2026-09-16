<template>
  <div class="h-full flex flex-col">
    <header class="px-3 py-2 border-b border-slate-800 bg-slate-900/40 backdrop-blur flex items-center justify-between">
      <h2 class="text-xs font-semibold tracking-wide uppercase text-slate-300">Infra LAN</h2>
      <button
        type="button"
        class="p-1 rounded text-slate-500 hover:text-white"
        title="Masquer"
        @click="toggleInfra"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 5l7 7-7 7M5 5l7 7-7 7" />
        </svg>
      </button>
    </header>
    <div class="flex-1 px-3 py-3 space-y-4 text-xs overflow-y-auto scrollbar-custom">
      <InfraLanPanel @ask="onInfraAsk" />
      <PendingApprovalsPanel />
    </div>
  </div>
</template>

<script setup>
import InfraLanPanel from './InfraLanPanel.vue'
import PendingApprovalsPanel from './PendingApprovalsPanel.vue'
import { useChat } from '../composables/useChat'
import { useLayout } from '../composables/useLayout'

const { queuePrompt } = useChat()
const { toggleInfra } = useLayout()

function onInfraAsk(text) {
  queuePrompt(text)
}
</script>

<script setup>
import ConversationList from './ConversationList.vue'
import { useLayout } from '../composables/useLayout'

const { toggleHist } = useLayout()
</script>

<template>
  <aside class="hidden sm:flex w-64 glass-panel border-r border-white/5 flex-col h-full z-20 shrink-0">
    <div class="px-4 py-3 flex items-center justify-between border-b border-white/5">
      <div>
        <p class="text-xs font-bold font-outfit text-white tracking-tight">Avec Compagnon</p>
        <p class="text-[9px] text-slate-500 uppercase tracking-widest">Discussions</p>
      </div>
      <button
        type="button"
        class="p-1.5 rounded-lg text-slate-500 hover:text-white hover:bg-white/5"
        title="Masquer"
        @click="toggleHist"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
        </svg>
      </button>
    </div>
    <div class="flex-1 overflow-y-auto scrollbar-custom min-h-0">
      <ConversationList />
    </div>
  </aside>
</template>

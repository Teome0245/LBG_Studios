<script setup>
import { RouterLink, useRouter } from 'vue-router'
import { useLayout } from '../composables/useLayout'
import { useChat } from '../composables/useChat'
import { PILOT_NAV } from '../lib/pilotLinks.js'

const { histCollapsed, toggleHist } = useLayout()
const { startNewChat } = useChat()
const router = useRouter()

function onNew() {
  startNewChat()
  if (router.currentRoute.value.path !== '/') router.push('/')
}
</script>

<template>
  <aside class="hidden sm:flex w-14 glass-panel border-r border-white/5 flex-col h-full z-30 items-center py-3 gap-2 shrink-0">
    <div class="h-8 w-8 rounded-lg bg-emerald-500 shadow-lg shadow-emerald-500/20 flex items-center justify-center mb-1">
      <span class="text-white font-bold font-outfit text-lg">L</span>
    </div>

    <button
      type="button"
      class="h-9 w-9 rounded-lg flex items-center justify-center text-slate-500 hover:text-white hover:bg-white/5"
      :title="histCollapsed ? 'Afficher l’historique' : 'Masquer l’historique'"
      @click="toggleHist"
    >
      <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path
          v-if="histCollapsed"
          stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
          d="M13 5l7 7-7 7M5 5l7 7-7 7"
        />
        <path
          v-else
          stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
          d="M11 19l-7-7 7-7m8 14l-7-7 7-7"
        />
      </svg>
    </button>

    <button
      type="button"
      class="h-9 w-9 rounded-lg flex items-center justify-center text-slate-400 hover:bg-emerald-500/15 hover:text-emerald-300"
      title="New Chat"
      @click="onNew"
    >
      <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
      </svg>
    </button>

    <router-link
      to="/lyra"
      class="h-9 w-9 rounded-lg flex items-center justify-center text-slate-500 hover:bg-white/5 hover:text-blue-300"
      active-class="!text-blue-400 bg-blue-500/10"
      title="Lyra Advanced"
    >
      <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
      </svg>
    </router-link>

    <router-link
      to="/brain"
      class="h-9 w-9 rounded-lg flex items-center justify-center text-slate-500 hover:bg-white/5 hover:text-emerald-400"
      active-class="!text-emerald-400 bg-emerald-500/10"
      title="Conscience 3D de Lyra"
    >
      <span class="text-base select-none">🧠</span>
    </router-link>

    <router-link
      to="/agents/map"
      class="h-9 w-9 rounded-lg flex items-center justify-center text-slate-500 hover:bg-white/5 hover:text-violet-300"
      active-class="!text-violet-300 bg-violet-500/10"
      title="Carte des agents"
    >
      <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
      </svg>
    </router-link>

    <router-link
      to="/providers/catalog"
      class="h-9 w-9 rounded-lg flex items-center justify-center text-slate-500 hover:bg-white/5 hover:text-cyan-300"
      active-class="!text-cyan-300 bg-cyan-500/10"
      title="Catalogue LLM"
    >
      <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
      </svg>
    </router-link>

    <div class="flex-1" />

    <div class="w-8 border-t border-white/10 my-1" />
    <a
      v-for="link in PILOT_NAV"
      :key="link.id"
      :href="link.href"
      target="_blank"
      rel="noopener noreferrer"
      class="h-9 w-9 rounded-lg flex items-center justify-center text-slate-500 hover:bg-amber-500/15 hover:text-amber-200"
      :title="link.title"
    >
      <span class="text-[9px] font-bold tracking-tight uppercase">{{ link.label.slice(0, 3) }}</span>
    </a>

    <div class="h-8 w-8 rounded-full bg-slate-800 border border-white/10 overflow-hidden" title="Stève Desh">
      <img src="https://ui-avatars.com/api/?name=SD&background=020617&color=fff" alt="User" />
    </div>
  </aside>
</template>

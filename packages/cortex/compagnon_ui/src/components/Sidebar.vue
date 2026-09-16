<script setup>
import { RouterLink } from 'vue-router'
import ConversationList from './ConversationList.vue'
import { useLayout } from '../composables/useLayout'
import { useChat } from '../composables/useChat'

const { leftCollapsed, toggleLeft } = useLayout()
const { startNewChat } = useChat()

function onNew() {
  startNewChat()
}
</script>

<template>
  <aside
    class="hidden sm:flex glass-panel border-r border-white/5 flex-col h-full z-20 transition-all duration-300 ease-out"
    :class="leftCollapsed ? 'w-16' : 'w-64'"
  >
    <div class="p-3 pb-2 flex items-center gap-2" :class="leftCollapsed ? 'justify-center flex-col' : 'px-4'">
      <div class="h-8 w-8 shrink-0 rounded-lg bg-emerald-500 shadow-lg shadow-emerald-500/20 flex items-center justify-center">
        <span class="text-white font-bold font-outfit text-xl">L</span>
      </div>
      <h1
        v-if="!leftCollapsed"
        class="text-xl font-bold font-outfit tracking-tight text-white flex-1 truncate"
      >Compagnon</h1>
      <button
        type="button"
        class="p-1.5 rounded-lg text-slate-500 hover:text-white hover:bg-white/5 transition-colors"
        :title="leftCollapsed ? 'Étendre la sidebar' : 'Réduire la sidebar'"
        @click="toggleLeft"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path
            v-if="leftCollapsed"
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
    </div>

    <!-- Mode réduit : icônes -->
    <nav v-if="leftCollapsed" class="flex-1 flex flex-col items-center gap-2 py-2 px-1">
      <button
        type="button"
        class="h-10 w-10 rounded-lg flex items-center justify-center text-slate-400 hover:bg-emerald-500/15 hover:text-emerald-300"
        title="New Chat"
        @click="onNew"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
      </button>
      <router-link
        to="/lyra"
        class="h-10 w-10 rounded-lg flex items-center justify-center text-slate-500 hover:bg-white/5 hover:text-blue-300"
        active-class="!text-blue-400 bg-blue-500/10"
        title="Lyra"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      </router-link>
      <router-link
        to="/agents/map"
        class="h-10 w-10 rounded-lg flex items-center justify-center text-slate-500 hover:bg-white/5 hover:text-violet-300"
        active-class="!text-violet-300 bg-violet-500/10"
        title="Agents"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
        </svg>
      </router-link>
      <router-link
        to="/providers/catalog"
        class="h-10 w-10 rounded-lg flex items-center justify-center text-slate-500 hover:bg-white/5 hover:text-cyan-300"
        active-class="!text-cyan-300 bg-cyan-500/10"
        title="LLM"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
        </svg>
      </router-link>
    </nav>

    <!-- Mode étendu -->
    <div v-else class="flex-1 overflow-y-auto scrollbar-custom min-h-0">
      <ConversationList />

      <nav class="px-3 pt-2 pb-4 space-y-1 border-t border-white/5 mt-2">
        <router-link
          to="/lyra"
          class="flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-medium transition-all hover:bg-white/5 text-slate-500 hover:text-white"
          active-class="bg-blue-500/10 text-blue-400 !text-blue-400"
        >
          Lyra Advanced
        </router-link>
        <router-link
          to="/agents/map"
          class="flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-medium transition-all hover:bg-white/5 text-slate-500 hover:text-white"
          active-class="bg-violet-500/10 text-violet-300 !text-violet-300"
        >
          Carte des agents
        </router-link>
        <router-link
          to="/providers/catalog"
          class="flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-medium transition-all hover:bg-white/5 text-slate-500 hover:text-white"
          active-class="bg-cyan-500/10 text-cyan-300 !text-cyan-300"
        >
          Catalogue LLM
        </router-link>
      </nav>
    </div>

    <div class="p-3 border-t border-white/5" :class="leftCollapsed ? 'flex justify-center' : ''">
      <div
        class="flex items-center gap-3 p-2 rounded-lg hover:bg-white/5 transition-colors"
        :class="leftCollapsed ? 'justify-center' : ''"
      >
        <div class="h-8 w-8 rounded-full bg-slate-800 border border-white/10 flex items-center justify-center overflow-hidden shrink-0">
          <img src="https://ui-avatars.com/api/?name=User&background=020617&color=fff" alt="User" />
        </div>
        <div v-if="!leftCollapsed" class="flex-1 min-w-0">
          <p class="text-xs font-semibold text-white truncate">Stève Desh</p>
          <p class="text-[10px] text-slate-500 truncate uppercase tracking-widest font-bold">Admin Pro</p>
        </div>
      </div>
    </div>
  </aside>
</template>

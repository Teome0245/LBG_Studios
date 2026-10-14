<script setup>
import NavRail from '../components/NavRail.vue'
import HistorySidebar from '../components/HistorySidebar.vue'
import ChatHeader from '../components/ChatHeader.vue'
import ChatFlow from '../components/ChatFlow.vue'
import ChatInput from '../components/ChatInput.vue'
import MonitoringPanel from '../components/MonitoringPanel.vue'
import InfraColumn from '../components/InfraColumn.vue'
import AgentsLivePanel from '../components/AgentsLivePanel.vue'
import CharacterDialsPanel from '../components/CharacterDialsPanel.vue'
import { useLayout } from '../composables/useLayout'

const {
  histCollapsed,
  infraCollapsed,
  monitorCollapsed,
  agentsLiveCollapsed,
  characterPanelOpen,
  closeCharacterPanel,
} = useLayout()
</script>

<template>
  <!-- Canal chat : rail + hist optionnel + fil ; colonnes droites uniquement si ouvertes -->
  <div class="flex h-full w-full overflow-hidden bg-slate-950 text-slate-200">
    <NavRail />

    <HistorySidebar v-if="!histCollapsed" />

    <div class="flex-1 flex flex-col relative min-w-0">
      <ChatHeader />
      <main class="flex-1 overflow-hidden flex flex-col relative">
        <ChatFlow />
        <ChatInput />
      </main>
    </div>

    <aside
      v-if="!agentsLiveCollapsed"
      class="hidden lg:flex w-64 glass-panel border-l border-white/5 flex-col h-full z-10 shrink-0"
      aria-label="Agents live"
    >
      <AgentsLivePanel />
    </aside>

    <aside
      v-if="!infraCollapsed"
      class="hidden lg:flex w-64 glass-panel border-l border-white/5 flex-col h-full z-10 shrink-0"
    >
      <InfraColumn />
    </aside>

    <aside
      v-if="!monitorCollapsed"
      class="hidden lg:flex w-72 glass-panel border-l border-white/5 flex-col h-full z-10 shrink-0"
    >
      <MonitoringPanel />
    </aside>

    <CharacterDialsPanel
      :open="characterPanelOpen"
      @close="closeCharacterPanel"
    />
  </div>
</template>

<style>
#app {
  height: 100vh;
  width: 100vw;
}
</style>

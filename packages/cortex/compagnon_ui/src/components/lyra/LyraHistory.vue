<template>
  <div class="bg-slate-900/60 border border-slate-700 rounded-xl p-4 shadow-lg h-full flex flex-col">
    <h2 class="text-xl font-semibold mb-3 flex items-center gap-2">
      <span>📜</span> Historique des variations
    </h2>

    <div class="flex-1 overflow-y-auto space-y-2 pr-1">
      <div
        v-for="(entry, index) in history"
        :key="index"
        class="text-sm bg-slate-800/40 border border-slate-700 rounded p-2"
      >
        <div class="text-slate-400 text-xs">{{ entry.timestamp }}</div>
        <div class="text-slate-200">{{ entry.message }}</div>
      </div>

      <p v-if="history.length === 0" class="text-slate-500 italic">
        Aucun événement pour le moment.
      </p>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  history: {
    type: Array,
    required: true,
    default: () => []
  }
});
</script>

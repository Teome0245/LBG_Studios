<template>
  <div class="bg-slate-900/60 border border-slate-700 rounded-xl p-4 shadow-lg">
    <h2 class="text-xl font-semibold mb-3 flex items-center gap-2">
      <span>🎭</span> Style comportemental actuel
    </h2>

    <p v-if="style" class="text-slate-200 leading-relaxed whitespace-pre-line">
      {{ style }}
    </p>

    <p v-else class="text-slate-500 italic">
      Chargement du style de Lyra…
    </p>
  </div>
</template>

<script setup>
const props = defineProps({
  style: {
    type: String,
    required: false,
    default: ""
  }
});
</script>

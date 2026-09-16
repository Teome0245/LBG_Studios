<template>
  <button
    class="inline-flex items-center gap-2 rounded-full border border-slate-700 bg-slate-900/80 px-3 py-1 text-xs hover:border-emerald-500/70 hover:text-emerald-300"
    @click="toggle"
  >
    <span v-if="isLight">🌙 Sombre</span>
    <span v-else>☀️ Clair</span>
  </button>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const isLight = ref(false)

onMounted(() => {
  isLight.value = document.documentElement.classList.contains('light')
})

function toggle() {
  isLight.value = !isLight.value
  document.documentElement.classList.toggle('light')
}
</script>




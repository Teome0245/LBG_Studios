<template>
  <div class="flex flex-col items-center">
    <!-- Icône -->
    <div class="text-3xl mb-2">{{ icon }}</div>

    <!-- Jauge verticale -->
    <div class="w-6 h-40 bg-slate-800 rounded relative overflow-hidden border border-slate-700">
      <div
        class="absolute bottom-0 left-0 w-full transition-all duration-300"
        :style="{
          height: value + '%',
          backgroundColor: color
        }"
      ></div>
    </div>

    <!-- Valeur -->
    <div class="mt-2 text-lg font-semibold">{{ value }}%</div>
  </div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  value: Number,
  icon: String
});

const color = computed(() => {
  if (props.value >= 70) return "#4ade80";   // vert
  if (props.value >= 40) return "#facc15";   // jaune
  return "#f87171";                          // rouge
});
</script>

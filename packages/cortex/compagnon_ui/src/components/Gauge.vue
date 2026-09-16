<template>
  <div class="flex flex-col gap-1">
    <div class="flex items-center justify-between text-[11px] text-slate-400">
      <span>{{ label }}</span>
      <span class="font-semibold text-slate-100">
        {{ value }}<span v-if="unit"> {{ unit }}</span>
      </span>
    </div>
    <div class="h-2 rounded-full bg-slate-800 overflow-hidden">
      <div
        class="h-full rounded-full bg-emerald-500 transition-all duration-500"
        :style="{ width: Math.min(100, value) + '%' }"
      />
    </div>
  </div>
</template>

<script setup>
defineProps({
  label: { type: String, required: true },
  value: { type: Number, required: true },
  unit: { type: String, default: '' },
})
</script>

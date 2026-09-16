<script setup>
import { useChat } from '../composables/useChat'

defineProps({
  followup: { type: Object, required: true },
})

const { queuePrompt } = useChat()

function onStep(step) {
  const reply = step?.reply || step?.hint
  if (reply) queuePrompt(reply)
}
</script>

<template>
  <div
    v-if="followup?.steps?.length"
    class="mt-3 flex flex-wrap gap-1.5"
  >
    <button
      v-for="(step, i) in followup.steps"
      :key="i"
      type="button"
      class="text-[11px] px-2.5 py-1 rounded-lg border border-white/15 bg-white/5 text-slate-300 hover:border-emerald-500/40 hover:text-emerald-200 transition-colors"
      :title="step.reply"
      @click="onStep(step)"
    >
      <span class="opacity-50 mr-1 uppercase text-[9px]">{{ step.env || 'lan' }}</span>
      {{ step.label || step.reply }}
    </button>
  </div>
</template>

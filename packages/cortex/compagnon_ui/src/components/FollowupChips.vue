<script setup>
import { useChat } from '../composables/useChat'

defineProps({
  followup: { type: Object, required: true },
})

const { queuePrompt } = useChat()

/** Enchaîne tout de suite (remplit + demande d’envoi via draft auto-send). */
function onStep(step) {
  const reply = step?.reply || step?.hint
  if (!reply) return
  queuePrompt(reply)
  // Signal pour auto-envoi (ChatInput écoute)
  try {
    window.dispatchEvent(new CustomEvent('compagnon:send-draft'))
  } catch {
    /* ignore */
  }
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
      class="text-[11px] px-2.5 py-1 rounded-lg border border-emerald-500/30 bg-emerald-500/10 text-emerald-100 hover:bg-emerald-500/20 transition-colors"
      :title="step.reply"
      @click="onStep(step)"
    >
      <span class="opacity-60 mr-1 uppercase text-[9px]">{{ step.env || 'go' }}</span>
      {{ step.label || step.reply }}
    </button>
  </div>
</template>

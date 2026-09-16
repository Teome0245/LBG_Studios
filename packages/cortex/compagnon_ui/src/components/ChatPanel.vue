<template>
  <div class="h-full flex flex-col">

    <!-- Header -->
    <header class="px-4 py-2 border-b border-slate-800 flex items-center justify-between">
      <h2 class="text-sm font-semibold tracking-wide uppercase">
        Conversation
      </h2>
    </header>

    <!-- Zone scrollable -->
    <div
      ref="chatContainer"
      class="flex-1 overflow-y-auto px-4 py-3 flex flex-col space-y-3 text-sm"
    >

      <div
        v-for="(msg, i) in messages"
        :key="i"
        class="flex items-start gap-3"
        :class="msg.role === 'user' ? 'justify-end' : 'justify-start'"
      >

        <!-- Icône (uniquement pour l'assistant) -->
        <div
          v-if="msg.role !== 'user'"
          class="flex-shrink-0 self-start mt-1"
        >
          <StateIcon :state="msg.state" />
        </div>

        <!-- Bulle -->
        <div
          class="max-w-[80%] rounded-xl px-3 py-2 text-sm message-bubble"
          :class="msg.role === 'user'
            ? 'message-user'
            : 'message-assistant'"
        >
          {{ msg.content }}
        </div>

      </div>

    </div>

  </div>
</template>

<script setup>
import { onUpdated, ref } from 'vue'
import { useChat } from '../composables/useChat.js'
import StateIcon from '@/components/StateIcon.vue'

const { messages } = useChat()
const chatContainer = ref(null)

onUpdated(() => {
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }
})
</script>

<style scoped>
.message-user {
  background: rgba(16,185,129,0.25);
  border: 1px solid rgba(16,185,129,0.4);
  backdrop-filter: blur(4px);
  color: #f8fafc;
  margin-right: 12px;
}

.message-assistant {
  background: rgba(59,130,246,0.25);
  border: 1px solid rgba(59,130,246,0.4);
  backdrop-filter: blur(4px);
  color: #f8fafc;
  margin-left: 12px;
}

.message-bubble {
  padding: 10px 14px;
  border-radius: 12px;
}
</style>
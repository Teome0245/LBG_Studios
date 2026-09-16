<template>
  <div class="flex items-end gap-3 w-full h-full">

    <!-- Champ de saisie -->
    <textarea
      v-model="input"
      rows="3"
      class="flex-1 resize-none rounded-lg px-3 py-2 text-sm input-zone
             placeholder:text-slate-400 focus:outline-none focus:ring-2
             focus:ring-emerald-500/70 focus:border-emerald-500"
      placeholder="Écris ta requête pour l’orchestrateur IA…"
      @keydown.enter.exact.prevent="send"
    />

    <!-- Bouton envoyer -->
    <button
      class="send-btn inline-flex items-center gap-2 rounded-lg px-4 py-2
             text-sm font-semibold shadow-sm"
      @click="send"
    >
      Envoyer
    </button>

  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useChat } from '../composables/useChat.js'
import { useApi } from '../composables/useApi.js'

const input = ref('')
const { addUserMessage, addMessage } = useChat()
const { sendPrompt } = useApi()

const send = async () => {
  if (!input.value.trim()) return

  const userMsg = input.value
  addUserMessage(userMsg)
  input.value = ""

  // Appel correct au backend /ask/
  const backendResponse = await sendPrompt(userMsg)

  // Le backend renvoie déjà un objet enrichi complet
  addMessage(backendResponse)
}
</script>

<style scoped>
.input-zone {
  background: rgba(0,0,0,0.45);
  border: 1px solid rgba(255,255,255,0.25);
  color: #f8fafc;
  border-radius: 10px;
  backdrop-filter: blur(4px);
}

.send-btn {
  background: linear-gradient(135deg, #10b981, #34d399);
  color: #0f172a;
  border: 1px solid rgba(16,185,129,0.6);
  transition: 0.15s ease-in-out;
}

.send-btn:hover {
  background: linear-gradient(135deg, #34d399, #6ee7b7);
  border-color: rgba(16,185,129,0.9);
  transform: translateY(-1px);
}
</style>


<script setup>
import { computed, ref } from 'vue'
import { useActivity } from '@/composables/useActivity'
import { PILOTAGE_BAR } from '@/lib/pilotageActions'
import { proposeAction } from '@/lib/agir'
import { useChat } from '@/composables/useChat'

const { current, toggleActivityOpen, clearActivity } = useActivity()
const { addUserMessage, addMessage, queuePrompt } = useChat()
const nextBusy = ref('')

const quickNext = computed(() => {
  if (!current.value) return []
  if (current.value.phase !== 'done' && current.value.phase !== 'error') return []
  const tools = (current.value.tools || []).join(' ')
  if (tools.includes('desktop') || tools.includes('agir')) {
    return PILOTAGE_BAR.filter((a) =>
      ['probe_ad', 'open_jobs', 'open_desktop', 'team_status'].includes(a.id)
    ).slice(0, 3)
  }
  return PILOTAGE_BAR.filter((a) =>
    ['probe_lan', 'team_status', 'open_jobs'].includes(a.id)
  ).slice(0, 3)
})

function lineClass(level) {
  if (level === 'ok') return 'text-emerald-400/90'
  if (level === 'warn') return 'text-amber-300/90'
  if (level === 'err') return 'text-red-400/90'
  return 'text-slate-400'
}

async function runQuick(a) {
  if (!a || nextBusy.value) return
  if (a.kind === 'link' && a.href) {
    window.open(a.href, '_blank', 'noopener,noreferrer')
    return
  }
  if (a.kind === 'ask' && a.prompt) {
    queuePrompt(a.prompt)
    try {
      window.dispatchEvent(new CustomEvent('compagnon:send-draft'))
    } catch {
      /* ignore */
    }
    return
  }
  if (a.kind !== 'agir' || !a.sourceText) return
  nextBusy.value = a.id
  addUserMessage(`Agir · ${a.label}`)
  try {
    const { proposal, reason } = await proposeAction(a.sourceText)
    if (!proposal) {
      addMessage({
        role: 'assistant',
        content: reason || 'Aucune action sûre.',
        source: 'agir',
      })
    } else {
      addMessage({
        role: 'assistant',
        content: proposal.summary || a.label,
        source: 'agir',
        actionProposal: proposal,
        actionSourceText: a.sourceText,
      })
    }
  } catch (e) {
    addMessage({
      role: 'assistant',
      content: String(e?.message || e),
      source: 'error',
    })
  } finally {
    nextBusy.value = ''
  }
}
</script>

<template>
  <div
    v-if="current"
    class="activity-encart"
    :data-phase="current.phase"
  >
    <button
      type="button"
      class="activity-head"
      @click="toggleActivityOpen"
    >
      <span class="activity-chevron" :class="{ closed: !current.open }">▾</span>
      <span class="activity-title">{{ current.title }}</span>
      <span
        v-for="t in current.tools"
        :key="t"
        class="activity-tool"
      >{{ t }}</span>
      <span class="activity-spacer" />
      <button
        type="button"
        class="activity-menu"
        title="Masquer"
        @click.stop="clearActivity"
      >···</button>
    </button>

    <div v-if="current.open" class="activity-body">
      <pre class="activity-log"><code
        v-for="(line, i) in current.lines"
        :key="i"
        :class="lineClass(line.level)"
      >{{ line.text }}{{ '\n' }}</code></pre>
    </div>

    <p
      class="activity-phase"
      :class="{
        'is-run': current.phase === 'running' || current.phase === 'planning',
        'is-ok': current.phase === 'done',
        'is-err': current.phase === 'error',
      }"
    >
      <span v-if="current.phase === 'running' || current.phase === 'planning'" class="activity-pulse" />
      {{ current.phaseLabel }}
    </p>

    <div v-if="quickNext.length" class="activity-next">
      <button
        v-for="a in quickNext"
        :key="a.id"
        type="button"
        class="activity-next-btn"
        :disabled="!!nextBusy"
        @click="runQuick(a)"
      >
        {{ nextBusy === a.id ? '…' : a.label }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.activity-encart {
  margin: 0.75rem 0 0.25rem;
  max-width: 40rem;
}
.activity-head {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  width: 100%;
  padding: 0.15rem 0.1rem;
  background: transparent;
  border: none;
  color: #cbd5e1;
  cursor: pointer;
  font-size: 0.78rem;
  text-align: left;
}
.activity-chevron {
  color: #64748b;
  font-size: 0.7rem;
  transition: transform 0.15s ease;
}
.activity-chevron.closed {
  transform: rotate(-90deg);
}
.activity-title {
  font-weight: 600;
  color: #e2e8f0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.activity-tool {
  font-size: 0.62rem;
  font-family: ui-monospace, monospace;
  color: #64748b;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 0.3rem;
  padding: 0.05rem 0.3rem;
}
.activity-spacer {
  flex: 1;
}
.activity-menu {
  border: none;
  background: transparent;
  color: #64748b;
  cursor: pointer;
  font-size: 0.85rem;
  letter-spacing: 0.05em;
  padding: 0 0.25rem;
}
.activity-menu:hover {
  color: #94a3b8;
}
.activity-body {
  margin-top: 0.25rem;
  border-radius: 0.65rem;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgb(15 23 42 / 0.72);
  padding: 0.55rem 0.75rem;
  max-height: 9.5rem;
  overflow: auto;
}
.activity-log {
  margin: 0;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 0.68rem;
  line-height: 1.45;
  white-space: pre-wrap;
  word-break: break-word;
}
.activity-phase {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  margin: 0.4rem 0 0;
  font-size: 0.72rem;
  color: #64748b;
}
.activity-phase.is-run {
  color: #94a3b8;
}
.activity-phase.is-ok {
  color: #34d399;
}
.activity-phase.is-err {
  color: #f87171;
}
.activity-pulse {
  width: 0.45rem;
  height: 0.45rem;
  border-radius: 50%;
  background: #38bdf8;
  box-shadow: 0 0 0 0 rgba(56, 189, 248, 0.5);
  animation: act-pulse 1.2s ease-out infinite;
}
@keyframes act-pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(56, 189, 248, 0.45);
  }
  70% {
    box-shadow: 0 0 0 6px rgba(56, 189, 248, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(56, 189, 248, 0);
  }
}
.activity-next {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
  margin-top: 0.45rem;
}
.activity-next-btn {
  font-size: 0.68rem;
  padding: 0.25rem 0.55rem;
  border-radius: 0.45rem;
  border: 1px solid rgba(45, 212, 191, 0.3);
  background: rgb(45 212 191 / 0.08);
  color: #99f6e4;
  cursor: pointer;
}
.activity-next-btn:hover:not(:disabled) {
  background: rgb(45 212 191 / 0.16);
}
.activity-next-btn:disabled {
  opacity: 0.45;
  cursor: default;
}
</style>

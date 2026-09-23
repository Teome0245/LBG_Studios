<script setup>
import { useInitiative } from '@/composables/useInitiative'

const { selfLine, lastSelf } = useInitiative()
</script>

<template>
  <div
    v-if="selfLine"
    class="self-strip"
    :title="lastSelf?.enabled ? 'Self-State Agency' : 'Self'"
    role="status"
  >
    <span class="self-dot" aria-hidden="true" />
    <span class="self-label">Self</span>
    <span class="self-text">{{ selfLine }}</span>
  </div>
</template>

<style scoped>
.self-strip {
  position: fixed;
  left: 50%;
  transform: translateX(-50%);
  bottom: 5.25rem;
  z-index: 55;
  max-width: min(36rem, calc(100vw - 2rem));
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.35rem 0.75rem;
  border-radius: 999px;
  border: 1px solid rgba(148, 163, 184, 0.25);
  background: rgba(15, 23, 42, 0.88);
  backdrop-filter: blur(10px);
  color: #cbd5e1;
  font-size: 0.7rem;
  line-height: 1.2;
  pointer-events: none;
}
.self-dot {
  width: 6px;
  height: 6px;
  border-radius: 999px;
  background: #2dd4bf;
  box-shadow: 0 0 8px rgba(45, 212, 191, 0.6);
  flex-shrink: 0;
}
.self-label {
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #5eead4;
  flex-shrink: 0;
}
.self-text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
@media (max-width: 640px) {
  .self-strip {
    bottom: 6.5rem;
    font-size: 0.65rem;
  }
}
</style>

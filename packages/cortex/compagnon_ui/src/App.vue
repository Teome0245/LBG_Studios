<template>
  <div
    v-if="!pilotBannerDismissed"
    class="cutover-banner"
    role="status"
  >
    <span class="cutover-text">
      <strong class="cutover-brand">Compagnon</strong>
      <span class="cutover-sep">·</span>
      Studio ops via
      <template v-for="(link, i) in PILOT_NAV" :key="link.id">
        <a
          :href="link.href"
          class="cutover-link"
          target="_blank"
          rel="noopener noreferrer"
          :title="link.title"
        >{{ link.label }}</a><span v-if="i < PILOT_NAV.length - 1" class="cutover-sep">·</span>
      </template>
    </span>
    <button
      type="button"
      class="cutover-dismiss"
      title="Masquer"
      @click="dismissPilotBanner"
    >✕</button>
  </div>
  <router-view />
  <LyraWidget />
  <SelfPresenceStrip />
  <InitiativeToast />
</template>

<script setup>
import { onMounted } from 'vue'
import LyraWidget from './components/LyraWidget.vue'
import SelfPresenceStrip from './components/SelfPresenceStrip.vue'
import InitiativeToast from './components/InitiativeToast.vue'
import { PILOT_NAV } from './lib/pilotLinks.js'
import { useLayout } from './composables/useLayout.js'
import { consumeAgirDeepLink } from './lib/consumeAgirDeepLink.js'

const { pilotBannerDismissed, dismissPilotBanner } = useLayout()

onMounted(() => {
  consumeAgirDeepLink()
})
</script>

<style scoped>
.cutover-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.28rem 0.85rem;
  background: rgb(15 23 42 / 0.88);
  color: #94a3b8;
  font-size: 0.75rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  z-index: 50;
  position: relative;
}
.cutover-brand {
  color: #5eead4;
  font-weight: 700;
  letter-spacing: 0.02em;
}
.cutover-text {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.2rem 0.35rem;
}
.cutover-link {
  color: #5eead4;
  text-decoration: none;
  font-weight: 600;
}
.cutover-link:hover {
  text-decoration: underline;
  text-underline-offset: 2px;
}
.cutover-sep {
  opacity: 0.45;
  margin: 0 0.1rem;
}
.cutover-dismiss {
  flex-shrink: 0;
  background: transparent;
  border: none;
  color: #64748b;
  cursor: pointer;
  font-size: 0.7rem;
  padding: 0.15rem 0.35rem;
  border-radius: 4px;
  font-family: inherit;
}
.cutover-dismiss:hover {
  color: #e2e8f0;
  background: rgba(255, 255, 255, 0.06);
}
</style>

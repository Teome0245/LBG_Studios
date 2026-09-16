<template>
  <div
    class="icon"
    :style="{
      width: '256px',
      height: '256px',
      backgroundImage: 'url(/assets/icons/256/sprite-256.png)',
      backgroundPosition: spriteMap[name]
    }"
  />
</template>

<script setup>
import spriteMap from '@/utils/iconSpriteMap.js'

defineProps({
  name: { type: String, required: true }
})
</script>

<style scoped>
.icon {
  background-size: 1024px 1024px; /* sprite 4x4 de 256px */
  background-repeat: no-repeat;
  background-color: transparent; /* important */
}
</style>
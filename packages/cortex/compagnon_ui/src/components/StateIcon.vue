<template>
  <MiniIcon :name="iconType" />
</template>

<script setup>
import { computed } from 'vue'
import MiniIcon from './MiniIcon.vue'
import { STATE_TO_ICON } from '@/utils/stateToIcon.js'

const props = defineProps({
  state: {
    type: String,
    required: true
  }
})

const iconType = computed(() => STATE_TO_ICON[props.state] ?? STATE_TO_ICON["unknown"])
</script>
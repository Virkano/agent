<template>
  <img src="@/assets/logo/logo.png" :height="height" />
</template>

<script setup lang="ts">
defineOptions({ name: 'LogoIcon' })

defineProps({
  height: {
    type: String,
    default: '36px',
  },
})
</script>

<template>
  <div />
</template>

<script setup lang="ts">

const props = defineProps<{
  value: unknown | null
  settings: unknown | null
}>();

const emit = defineEmits<{(e: 'input', value: unknown): void
}>();

</script>

<style scoped lang="scss">

</style>

<template>
  <div>
    <span>Тут будет интересный текст</span>
  </div>
</template>

<script setup lang="ts">

import { FileFieldSettings } from '@/types/Descriptive/Fields/FileField';

const props = defineProps<{
  value: unknown | null
  settings: FileFieldSettings | null
}>();

const emit = defineEmits<{(e: 'input', value: FileFieldSettings): void
}>();

</script>

<style scoped lang="scss">

</style>

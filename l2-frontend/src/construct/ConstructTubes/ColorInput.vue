<template>
  <div :style="`background-color: ${localColor}`">
    <input
      v-model="localColor"
      class="nbr color-input"
      type="color"
    >
  </div>
</template>

<script setup lang="ts">

import { ref, watch } from 'vue';

const props = defineProps({
  value: {
    type: String,
  },
});

const emit = defineEmits(['input']);

const localColor = ref('');

watch(() => props.value, () => {
  localColor.value = props.value;
}, { immediate: true });

watch(localColor, () => {
  emit('input', localColor.value);
});
</script>

<style scoped lang="scss">
.color-input {
  border: 0;
  background: none;
  padding: 0;
  margin: 0;
  height: 33px;
  opacity: 0;
}
</style>

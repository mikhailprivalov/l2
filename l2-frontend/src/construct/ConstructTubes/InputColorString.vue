<template>
  <div class="flex">
    <input
      v-model="localColor"
      class="form-control nbr"
      maxlength="7"
    >
    <ColorInput
      v-model="localColor"
    />
  </div>
</template>

<script setup lang="ts">

import { ref, watch } from 'vue';

import ColorInput from '@/construct/ConstructTubes/ColorInput.vue';

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
.flex {
  display: flex;
}
</style>

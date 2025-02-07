<template>
  <div class="flex">
    <RegexFormatInput
      v-model="localColor"
      :rules="/^#[0-9A-Fa-f]{0,6}$/"
      :reverse-mode="true"
      class="form-control nbr"
    />
    <ColorInput
      v-model="localColor"
    />
  </div>
</template>

<script setup lang="ts">

import { ref, watch } from 'vue';

import ColorInput from '@/construct/ConstructTubes/ColorInput.vue';
import RegexFormatInput from '@/construct/RegexFormatInput.vue';

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

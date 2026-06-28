<template>
  <input
    v-model="content"
  >
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';

const props = defineProps<{
  value?: string;
  rules: RegExp;
  reverseMode?: boolean;
}>();

const emit = defineEmits(['input']);

const content = ref('');

watch(
  () => props.value,
  () => {
    content.value = props.value ?? '';
  },
  { immediate: true },
);

watch(content, () => {
  if (!props.reverseMode) {
    const newContent = content.value.replace(props.rules, '');
    if (newContent === content.value) {
      emit('input', content.value);
    } else {
      content.value = newContent;
    }
  } else {
    const newContentValid = props.rules.test(content.value);
    if (!newContentValid) {
      content.value = content.value.slice(0, -1);
    } else {
      emit('input', content.value);
    }
  }
});
</script>

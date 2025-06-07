<template>
  <div>
    <input
      v-model="searchValue"
      class="form-control nbr"
      @input="debouncedInput"
    >
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { debounce } from 'lodash';

const emit = defineEmits(['input']);

const searchValue = ref('');

const input = () => {
  emit('input', searchValue.value);
};
const debouncedInput = debounce(input, 300);
</script>

<style scoped lang="scss">
</style>

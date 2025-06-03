<template>
  <div class="column-row">
    <p class="column-text">
      {{ props.columnText }}
    </p>
    <input
      v-model="searchValue"
      class="form-control"
      @input="debouncedInput"
    >
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { debounce } from 'lodash';

const props = defineProps({
  columnText: {
    type: String,
    required: true,
  },
});

const emit = defineEmits(['input']);

const searchValue = ref('');

const input = () => {
  emit('input', searchValue.value);
};
const debouncedInput = debounce(input, 300);
</script>

<style scoped lang="scss">
.column-row {
  display: flex;
  gap: 2px
}
.column-text {
  margin: 7px 0;
}
</style>

<template>
  <div class="column-row">
    <p class="column-text">
      {{ props.columnText }}
    </p>
    <input
      v-model="searchValue"
      class="form-control"
    >
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

const props = defineProps({
  columnText: {
    type: String,
    required: true,
  },
});

const searchValue = ref('');
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

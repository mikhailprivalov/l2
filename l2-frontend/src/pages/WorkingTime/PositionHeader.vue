<template>
  <div class="column-row">
    <p class="column-text">
      {{ props.columnText }}
    </p>
    <i class="fa fa-filter column-icon" />
  </div>
</template>

<script setup lang="ts">
const props = defineProps({
  columnText: {
    type: String,
    required: true,
  },
});
</script>

<style scoped lang="scss">
.column-row {
  display: flex;
  gap: 2px;
  padding: 7px 0;
}
.column-text {
  margin: 0;
}
.column-icon {
  padding: 3px;
  color: #636e7e;
}
</style>

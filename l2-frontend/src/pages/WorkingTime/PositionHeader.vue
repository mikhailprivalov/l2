<template>
  <div>
    <p>{{ props.columnText }}</p>
    <i class="fa fa-filter" />
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

</style>

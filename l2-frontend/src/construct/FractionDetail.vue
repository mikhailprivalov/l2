<template>
  <div class="fraction-detail">
    <label>По умолчанию</label>
    <input class="form-control">
  </div>
</template>

<script setup lang="ts">
const props = defineProps({
  fractionPk: {
    type: Number,
    required: true,
  },
});
</script>

<style scoped lang="scss">
.fraction-detail {
  background-color: #fff;
  border-radius: 4px;
  overflow-y: auto;
}
</style>

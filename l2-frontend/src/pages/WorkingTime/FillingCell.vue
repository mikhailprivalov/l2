<template>
  <div class="flex">
    <button
      class="btn btn-blue-nb"
      @click="fill"
    >
      Заполнить по шаблону
    </button>
    <button
      class="btn btn-blue-nb"
      @click="clear"
    >
      Очистить шаблон
    </button>
  </div>
</template>

<script setup lang="ts">

const emit = defineEmits(['fill', 'clear']);

const fill = () => {
  emit('fill');
};
const clear = () => {
  emit('clear');
};
</script>

<style scoped lang="scss">
.flex {
  display: flex;
}
</style>

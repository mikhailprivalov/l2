<template>
  <div>
    <button
      class="btn btn-blue-nb"
      @click="fill"
    >
      Заполнить по шаблону
    </button>
  </div>
</template>

<script setup lang="ts">

const emit = defineEmits(['fill']);

const fill = () => {
  emit('fill');
};

</script>

<style scoped lang="scss">

</style>

<template>
  <div>
    <div class="sidebar">
      <div>
        <RadioFieldById
          :variants="filterButtons"
          item-width="33%"
          item-height="25px"
          :auto-height="true"
        />
      </div>
    </div>
    <div class="filters-panel">
      <input
        class="form-control filters-input"
        placeholder="Исполнитель"
      >
      <input
        class="form-control filters-input"
        placeholder="Контроль до"
      >
      <input
        class="form-control filters-input"
        placeholder="Фильтр 3"
      >
      <input
        class="form-control filters-input"
        placeholder="фильтр 4"
      >
    </div>
  </div>
</template>

<script setup lang="ts">

import { ref } from 'vue';

import RadioFieldById from '@/fields/RadioFieldById.vue';

const filterButtons = ref([
  { id: 'created', label: 'Я создал' },
  { id: 'doing', label: 'Я исполняю' },
  { id: 'wrote', label: 'Я поручил' },
  { id: 'onControl', label: 'Я контролирую' },
  { id: 'toBeAgreed', label: 'Мне согласовать' },
  { id: 'onSignature', label: 'Мне подписать' },
]);
</script>

<style scoped lang="scss">
.sidebar {
  display: flex;
  flex-direction: column;
  background-color: #f8f7f7;
  border-right: 1px solid #b1b1b1;
}
.filters-panel {
  display: flex;
  flex-direction: row;
  background-color: #f8f7f7;
}

.filters-input {
  height: 25px;
  border-radius: 0;
}
</style>

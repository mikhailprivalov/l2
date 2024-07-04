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
      <div>
        <label class="filters-label">Исполнитель</label>
        <input class="form-control filters-input">
      </div>
      <div>
        <label class="filters-label">Срок контроля</label>
        <input class="form-control filters-input">
      </div>
      <div>
        <label class="filters-label">Фильтр 3</label>
        <input class="form-control filters-input">
      </div>
      <div>
        <label class="filters-label">Фильтр 4</label>
        <input class="form-control filters-input">
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">

import { ref } from 'vue';

import RadioFieldById from '@/fields/RadioFieldById.vue';

const filterButtons = ref([
  { id: 'my', label: 'Мои' },
  { id: 'wrote', label: 'Отписал' },
  { id: 'onControl', label: 'На контроле' },
  { id: 'toBeAgreed', label: 'На согласовании' },
  { id: 'onSignature', label: 'На подписи' },
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
.filters-label {
  margin-bottom: 0;
  height: 25px;
}
.filters-input {
  height: 25px;
}
</style>

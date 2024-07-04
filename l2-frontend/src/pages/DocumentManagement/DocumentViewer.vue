<template>
  <div>
    <div class="two-col-filters">
      <div class="sidebar">
        <div class="flex row-border">
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
    <div class="two-col">
      <div class="sidebar">
        <DocumentsExplorer />
      </div>
      <div class="viewer">
        <div class="filters-panel document-panel" />
        <div>
          <h6>сам документ</h6>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">

import { ref } from 'vue';

import RadioFieldById from '@/fields/RadioFieldById.vue';
import DocumentsExplorer from '@/pages/DocumentManagement/DocumentsExplorer.vue';

const filterButtons = ref([
  { id: 'my', label: 'Мои' },
  { id: 'wrote', label: 'Отписал' },
  { id: 'onControl', label: 'На контроле' },
  { id: 'toBeAgreed', label: 'На согласовании' },
  { id: 'onSignature', label: 'На подписи' },
]);

</script>

<style scoped lang="scss">
.two-col {
  display: grid;
  grid-template-columns: minmax(200px, 380px) minmax(150px, auto);
  height: calc(100vh - 36px);
}
.sidebar {
  display: flex;
  flex-direction: column;
  background-color: #f8f7f7;
  border-right: 1px solid #b1b1b1;
}

.two-col-filters {
  display: grid;
  grid-template-columns: minmax(200px, 380px) minmax(150px, auto);
  height: 50px;
}
.filters-panel {
  display: flex;
  flex-direction: row;
  background-color: #f8f7f7;
}
.document-panel {
  height: 34px;
  border-top: 1px solid #b1b1b1;
  border-bottom: 1px solid #b1b1b1;
}
.filters-label {
  margin-bottom: 0;
  height: 25px;
}
.filters-input {
  height: 25px;
}

</style>

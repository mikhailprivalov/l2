<template>
  <div>
    <div class="two-col-filters">
      <div class="sidebar">
        <h6>фильтры</h6>
      </div>
      <div class="filters-panel">
        <h6>ещё фильтры</h6>
      </div>
    </div>
    <div class="two-col">
      <div class="sidebar">
        <DocumentsExplorer />
      </div>
      <div class="viewer">
        <h4>Просмотрщик</h4>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">

import DocumentsExplorer from '@/pages/DocumentManagement/DocumentsExplorer.vue';

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
  border-bottom: 1px solid #b1b1b1;
}

</style>

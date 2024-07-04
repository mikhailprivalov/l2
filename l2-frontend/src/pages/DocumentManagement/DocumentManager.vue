<template>
  <div>
    <DocumentsFilters class="two-col-filters" />
    <div class="two-col">
      <div class="sidebar">
        <DocumentsExplorer />
      </div>
      <div class="viewer">
        <DocumentViewer />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">

import DocumentsExplorer from '@/pages/DocumentManagement/DocumentsExplorer.vue';
import DocumentsFilters from '@/pages/DocumentManagement/DocumentsFilters.vue';
import DocumentViewer from '@/pages/DocumentManagement/DocumentViewer.vue';

</script>

<style scoped lang="scss">
.two-col {
  display: grid;
  grid-template-columns: minmax(200px, 380px) minmax(150px, auto);
  height: calc(100vh - 86px);
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
</style>

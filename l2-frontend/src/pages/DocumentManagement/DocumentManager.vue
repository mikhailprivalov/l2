<template>
  <div>
    <DocumentsFilters
      class="two-col-filters"
      @update:filter="roleFilter = $event"
    />
    <div class="two-col">
      <div class="sidebar">
        <DocumentsExplorer
          :role-filter="roleFilter"
          @select="selectedDocumentId = $event"
        />
      </div>
      <div class="viewer">
        <DocumentViewer :document-id="selectedDocumentId" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

import DocumentsExplorer from '@/pages/DocumentManagement/DocumentsExplorer.vue';
import DocumentsFilters from '@/pages/DocumentManagement/DocumentsFilters.vue';
import DocumentViewer from '@/pages/DocumentManagement/DocumentViewer.vue';

const selectedDocumentId = ref<number | null>(null);
const roleFilter = ref<string | null>(null);

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
  min-height: 0;
  overflow: hidden;
  background-color: #f8f7f7;
  border-right: 1px solid #b1b1b1;
}
.viewer {
  min-height: 0;
  overflow: hidden;
}
.two-col-filters {
  display: grid;
  grid-template-columns: minmax(200px, 380px) minmax(150px, auto);
  height: 50px;
}
</style>

<template>
  <div>
    <DocumentsFilters
      class="two-col-filters"
      :filter="roleFilter"
      @update:filter="roleFilter = $event"
      @search="onSearch"
    />
    <div class="two-col">
      <div class="sidebar">
        <DocumentsExplorer
          :role-filter="roleFilter"
          :list-refresh="listRefresh"
          :count-refresh="countRefresh"
          :found-document="foundDocument"
          @select="selectedDocumentId = $event"
          @update:filter="roleFilter = $event"
        />
      </div>
      <div class="viewer">
        <DocumentViewer
          :document-id="selectedDocumentId"
          @visibility-change="onVisibilityChange"
          @reviewed="onReviewed"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { getCurrentInstance, ref } from 'vue';

import { useStore } from '@/store';
import * as actions from '@/store/action-types';
import api from '@/api';
import DocumentsExplorer from '@/pages/DocumentManagement/DocumentsExplorer.vue';
import DocumentsFilters from '@/pages/DocumentManagement/DocumentsFilters.vue';
import DocumentViewer from '@/pages/DocumentManagement/DocumentViewer.vue';

const store = useStore();
const root = getCurrentInstance().proxy.$root;
const selectedDocumentId = ref<number | null>(null);
const roleFilter = ref<string | null>(null);
const listRefresh = ref(0);
const countRefresh = ref(0);
const foundDocument = ref<{ id: number; title: string } | null>(null);

const onVisibilityChange = () => {
  listRefresh.value += 1;
};

const onReviewed = () => {
  countRefresh.value += 1;
};

const onSearch = async (q: string) => {
  await store.dispatch(actions.INC_LOADING);
  try {
    const data = await api('document-manager/documents/find', { id: Number(q) });
    if (data?.ok) {
      foundDocument.value = { id: data.id, title: data.title };
      selectedDocumentId.value = data.id;
    } else {
      root.$emit('msg', 'error', data?.message || 'Документ не найден');
    }
  } finally {
    await store.dispatch(actions.DEC_LOADING);
  }
};

</script>

<style scoped lang="scss">
.two-col {
  display: grid;
  grid-template-columns: minmax(200px, 380px) minmax(150px, auto);
  height: calc(100vh - 70px);
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
  height: 34px;
}
</style>

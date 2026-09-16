<template>
  <PageInnerLayout>
    <TwoSidedLayout
      :left-width-px="leftWidthPx"
      :min-left-width-px="MIN_LEFT_WIDTH_PX"
      :min-right-width-px="MIN_RIGHT_WIDTH_PX"
      resizable
      @update:left-width-px="onLeftWidthChange"
    >
      <template #left>
        <div class="pane">
          <DocumentsFilters
            class="filters-top"
            part="search"
            :filter="roleFilter"
            @update:filter="roleFilter = $event"
            @search="onSearch"
          />
          <DocumentsExplorer
            class="explorer-fill"
            :role-filter="roleFilter"
            :list-refresh="listRefresh"
            :count-refresh="countRefresh"
            :found-document="foundDocument"
            @select="selectedDocumentId = $event"
            @update:filter="roleFilter = $event"
          />
        </div>
      </template>
      <template #right>
        <div class="pane pane-right">
          <DocumentsFilters
            class="filters-top"
            part="filters"
            :filter="roleFilter"
            @update:filter="roleFilter = $event"
          />
          <div class="viewer">
            <DocumentViewer
              :document-id="selectedDocumentId"
              @visibility-change="onVisibilityChange"
              @reviewed="onReviewed"
            />
          </div>
        </div>
      </template>
    </TwoSidedLayout>
  </PageInnerLayout>
</template>

<script setup lang="ts">
import { getCurrentInstance, ref, watch } from 'vue';

import { useStore } from '@/store';
import * as actions from '@/store/action-types';
import api from '@/api';
import PageInnerLayout from '@/layouts/PageInnerLayout.vue';
import TwoSidedLayout from '@/layouts/TwoSidedLayout.vue';
import DocumentsExplorer from '@/pages/DocumentManagement/DocumentsExplorer.vue';
import DocumentsFilters from '@/pages/DocumentManagement/DocumentsFilters.vue';
import DocumentViewer from '@/pages/DocumentManagement/DocumentViewer.vue';

const DEFAULT_LEFT_WIDTH_PX = 380;
const MIN_LEFT_WIDTH_PX = 200;
const MIN_RIGHT_WIDTH_PX = 150;
const LEFT_WIDTH_STORAGE_KEY = 'document-manager-left-width';

const readStoredLeftWidth = (): number => {
  try {
    const value = Number(localStorage.getItem(LEFT_WIDTH_STORAGE_KEY));
    if (Number.isFinite(value) && value >= MIN_LEFT_WIDTH_PX) {
      return value;
    }
  } catch {
    // ignore storage errors
  }
  return DEFAULT_LEFT_WIDTH_PX;
};

const store = useStore();
const root = getCurrentInstance().proxy.$root;
const selectedDocumentId = ref<number | null>(null);
const roleFilter = ref<string | null>(null);
const listRefresh = ref(0);
const countRefresh = ref(0);
const foundDocument = ref<{ id: number; title: string } | null>(null);
const leftWidthPx = ref(readStoredLeftWidth());

const onLeftWidthChange = (value: number) => {
  leftWidthPx.value = value;
};

watch(leftWidthPx, value => {
  try {
    localStorage.setItem(LEFT_WIDTH_STORAGE_KEY, String(value));
  } catch {
    // ignore storage errors
  }
});

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
.pane {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  overflow: hidden;
  background-color: #f8f7f7;
}

.pane-right {
  background-color: #fff;
}

.filters-top {
  flex: 0 0 auto;
}

.explorer-fill {
  flex: 1 1 0;
  min-height: 0;
  overflow: hidden;
}

.viewer {
  flex: 1 1 0;
  min-height: 0;
  overflow: hidden;
}
</style>

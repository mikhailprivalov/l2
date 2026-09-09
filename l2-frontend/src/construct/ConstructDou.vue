<template>
  <div class="three-col">
    <div class="panel panel-nav">
      <div
        v-for="button in navButtons"
        :key="button.id"
        class="row-border"
      >
        <button
          class="transparent-button"
          :class="{ 'active-button': selectedNavId === button.id }"
          type="button"
          @click="selectNav(button.id)"
        >
          {{ button.title }}
        </button>
      </div>
    </div>
    <div class="panel panel-middle">
      <template v-if="isWorkingSection">
        <input
          v-model="titleFilter"
          class="form-control search-input"
          placeholder="Фильтр по названию"
        >
        <div
          class="sidebar-content"
          :class="{ fcenter: filteredItems.length === 0 }"
        >
          <div v-if="filteredItems.length === 0">
            Не найдено
          </div>
          <div
            v-for="row in filteredItems"
            :key="row.id"
            class="research"
            :class="{ active: selectedId === row.id }"
            @click="selectedId = row.id"
          >
            <div class="research-head">
              {{ row.title }}
            </div>
            <div
              v-if="row.groupTitle"
              class="research-sub"
            >
              {{ row.groupTitle }}
            </div>
          </div>
        </div>
        <button
          v-if="canAdd"
          class="btn btn-blue-nb sidebar-footer"
          type="button"
          @click="addItem"
        >
          <i class="glyphicon glyphicon-plus" />
          Добавить
        </button>
      </template>
    </div>
    <div class="panel panel-main">
      <DouCatalogEditor
        v-if="showCatalogEditor"
        :key="`${selectedNavId}-${selectedId}`"
        :kind="catalogKind"
        :item-id="selectedId"
        :title-value="selectedItem?.title"
        :code-value="selectedItem?.code"
        :group-id-value="selectedItem?.groupId"
        :groups="groups"
        @saved="onCatalogSaved"
        @cancel="selectedId = null"
      />
      <DouDocumentStructureEditor
        v-else-if="showStructureEditor"
        :key="selectedId"
        :type-document-id="selectedId"
        @saved="onStructureSaved"
        @cancel="selectedId = null"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  computed, onMounted, ref, watch,
} from 'vue';

import { useStore } from '@/store';
import * as actions from '@/store/action-types';
import api from '@/api';
import DouCatalogEditor from '@/construct/DouCatalogEditor.vue';
import DouDocumentStructureEditor from '@/construct/DouDocumentStructureEditor.vue';

interface NavButton {
  id: string;
  title: string;
}

interface CatalogItem {
  id: number;
  title: string;
  code?: string;
  groupId?: number | null;
  groupTitle?: string;
}

const WORKING_NAV = ['document_groups', 'document_types', 'skeleton'];

const store = useStore();
const navButtons = ref<NavButton[]>([]);
const selectedNavId = ref<string | null>(null);
const titleFilter = ref('');
const items = ref<CatalogItem[]>([]);
const groups = ref<CatalogItem[]>([]);
const selectedId = ref<number | null>(null);

const isWorkingSection = computed(() => WORKING_NAV.includes(selectedNavId.value || ''));
const canAdd = computed(() => selectedNavId.value === 'document_groups' || selectedNavId.value === 'document_types');
const catalogKind = computed<'group' | 'type'>(() => (selectedNavId.value === 'document_groups' ? 'group' : 'type'));

const filteredItems = computed(() => {
  const search = titleFilter.value.trim().toLowerCase();
  if (!search) {
    return items.value;
  }
  return items.value.filter(row => (row.title || '').toLowerCase().includes(search));
});

const selectedItem = computed(() => items.value.find(row => row.id === selectedId.value) || null);

const showCatalogEditor = computed(
  () => (selectedNavId.value === 'document_groups' || selectedNavId.value === 'document_types')
    && selectedId.value !== null,
);

const showStructureEditor = computed(
  () => selectedNavId.value === 'skeleton' && selectedId.value !== null && selectedId.value > 0,
);

const loadNavButtons = async () => {
  await store.dispatch(actions.INC_LOADING);
  try {
    const { result } = await api('construct/dou/get-nav-buttons');
    navButtons.value = result || [];
    if (navButtons.value.length > 0 && !selectedNavId.value) {
      selectedNavId.value = navButtons.value[0].id;
    }
  } finally {
    await store.dispatch(actions.DEC_LOADING);
  }
};

const loadGroups = async () => {
  const { result } = await api('document-manager/groups/list');
  groups.value = result || [];
};

const loadItems = async () => {
  selectedId.value = null;
  items.value = [];
  if (!isWorkingSection.value) {
    return;
  }
  await store.dispatch(actions.INC_LOADING);
  try {
    if (selectedNavId.value === 'document_groups') {
      const { result } = await api('document-manager/groups/list');
      items.value = result || [];
    } else {
      await loadGroups();
      const { result } = await api('document-manager/types/list');
      items.value = result || [];
    }
  } finally {
    await store.dispatch(actions.DEC_LOADING);
  }
};

const selectNav = (id: string) => {
  selectedNavId.value = id;
};

const addItem = () => {
  selectedId.value = -1;
};

const onCatalogSaved = async (payload: { id: number }) => {
  await loadItems();
  selectedId.value = payload.id;
};

const onStructureSaved = async () => {
  await loadItems();
};

watch(selectedNavId, () => {
  titleFilter.value = '';
  loadItems();
});

onMounted(() => {
  loadNavButtons();
});
</script>

<style scoped lang="scss">
.three-col {
  display: grid;
  grid-template-columns: 1fr 1fr 5.56fr;
  height: calc(100vh - 36px);
  margin-bottom: 5px;
}

.panel {
  display: flex;
  flex-direction: column;
  background-color: #f8f7f7;
  border-right: 1px solid #b1b1b1;
}

.panel-nav {
  overflow-y: auto;
}

.panel-middle {
  overflow: hidden;
}

.panel-main {
  border-right: none;
  overflow: hidden;
  background-color: #f8f7f7;
}

.row-border {
  border-bottom: 1px solid #b1b1b1;
  display: flex;
}

.row-border:first-child {
  border-top: 1px solid #b1b1b1;
}

.transparent-button {
  background-color: transparent;
  color: #434A54;
  flex: 1;
  border: none;
  padding: 6px 10px;
  text-align: left;
  cursor: pointer;
}

.transparent-button:hover {
  background-color: #434a54;
  color: #FFFFFF;
}

.transparent-button:active {
  background-color: #37BC9B;
  color: #FFFFFF;
}

.active-button {
  background-color: #049372;
  color: #FFFFFF;
}

.search-input {
  border-radius: 0;
  border-left: none;
  border-right: none;
  height: 34px;
  flex: 0 0 34px;
}

.sidebar-content {
  flex: 1;
  overflow-y: auto;
  background-color: hsla(30, 3%, 97%, 1);
}

.sidebar-content:not(.fcenter) {
  padding-bottom: 10px;
}

.fcenter {
  display: flex;
  align-items: center;
  justify-content: center;
}

.sidebar-footer {
  flex: 0 0 34px;
  border-radius: 0;
  margin: 0;
}

.research {
  background-color: #fff;
  margin: 10px;
  border-radius: 4px;
  cursor: pointer;
  overflow: hidden;
  border: 2px solid transparent;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
  transition: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1);
  position: relative;

  &:hover {
    box-shadow: 0 14px 28px rgba(0, 0, 0, 0.25), 0 10px 10px rgba(0, 0, 0, 0.22);
    z-index: 1;
    transform: scale(1.008);
  }

  &.active {
    border-color: #049372;

    .research-head {
      background-color: #049372;
      color: #FFFFFF;
    }
  }
}

.research:not(:first-child) {
  margin-top: 0;
}

.research:last-child {
  margin-bottom: 0;
}

.research-head {
  padding: 5px 8px;
}

.research-sub {
  padding: 3px 8px 6px;
  font-size: 12px;
  color: #6c7a89;
  background-color: #f3f6f4;
}
</style>

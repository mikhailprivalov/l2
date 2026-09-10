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
        <div class="middle-search">
          <input
            v-model="titleFilter"
            type="text"
            class="form-control nbr"
            placeholder="Фильтр по названию"
          >
          <button
            v-if="canAdd"
            class="btn btn-blue-nb nbr nba"
            type="button"
            @click="addItem"
          >
            Добавить
          </button>
        </div>
        <div
          class="item-list"
          :class="{ 'item-list--empty': filteredItems.length === 0 }"
        >
          <div v-if="filteredItems.length === 0">
            Не найдено
          </div>
          <div
            v-for="row in filteredItems"
            :key="row.id"
            class="object-row"
            :class="{ 'object-row--active': selectedId === row.id }"
            role="button"
            tabindex="0"
            @click="selectedId = row.id"
            @keydown.enter.prevent="selectedId = row.id"
            @keydown.space.prevent="selectedId = row.id"
          >
            <span class="object-row__label">{{ row.title }}</span>
            <span
              v-if="row.groupTitle"
              class="object-row__sub"
            >
              {{ row.groupTitle }}
            </span>
          </div>
        </div>
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

.middle-search {
  display: flex;
  flex-direction: row;
  align-items: stretch;
  flex-wrap: nowrap;
  flex: 0 0 34px;
  min-width: 0;
  height: 34px;
  min-height: 34px;
  max-height: 34px;
  border-bottom: 1px solid #b1b1b1;

  :deep(input.form-control),
  :deep(.btn) {
    align-self: stretch;
    border-radius: 0 !important;
    -webkit-border-radius: 0 !important;
    -moz-border-radius: 0 !important;
  }

  :deep(input.form-control) {
    border: none;
    box-shadow: none;
    width: auto !important;
    flex: 2 166px;
    min-width: 0;
  }

  :deep(.btn) {
    flex: 3 94px;
    width: 94px;
    border-top: none !important;
    border-bottom: none !important;
    border-right: none !important;
    margin: 0;
  }
}

.item-list {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
  padding: 0;
  margin: 0;
}

.item-list--empty {
  display: flex;
  align-items: center;
  justify-content: center;
}

.object-row {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 100%;
  box-sizing: border-box;
  height: 34px;
  min-height: 34px;
  line-height: 22px;
  border: none;
  border-bottom: 1px solid #b1b1b1;
  border-radius: 0;
  background-color: transparent;
  color: #434A54;
  padding: 0 6px 0 10px;
  text-align: left;
  cursor: pointer;
  outline: none;
  box-shadow: none;
}

.object-row__label {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.object-row__sub {
  flex-shrink: 1;
  max-width: 45%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 12px;
  opacity: 0.85;
}

.object-row:hover {
  background-color: #434a54;
  color: #FFFFFF;
}

.object-row--active,
.object-row--active:hover {
  background-color: #049372;
  color: #FFFFFF;
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
</style>

<style lang="scss">
.three-col .middle-search .btn.btn-blue-nb {
  border-radius: 0 !important;
  -webkit-border-radius: 0 !important;
  -moz-border-radius: 0 !important;
}

.three-col .object-row,
.three-col .object-row--active {
  border-radius: 0 !important;
  -webkit-border-radius: 0 !important;
  -moz-border-radius: 0 !important;
}
</style>
